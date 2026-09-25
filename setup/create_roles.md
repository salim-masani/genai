# AWS setup: roles, resources, and privileges

This guide gives you copy-paste commands to create the IAM roles and resources
the notebooks need, plus the exact privileges each demo requires. Everything
here uses placeholders you replace with your own values.

> **Cost warning:** the AWS paths in these notebooks create billable resources
> (S3 objects, Glue crawlers and Data Quality runs, Lambda, KMS calls,
> Comprehend, Bedrock model invocations). Run cleanup cells after class and
> delete anything you no longer need.

## 0. One-time prerequisites

1. Install the AWS CLI v2 and sign in. SSO is recommended:
   ```
   aws sso login --profile training
   ```
2. Install Python 3.10+ and, in a virtual environment, the Python packages:
   ```
   python -m pip install -r requirements.txt
   ```
3. Set the values you will reuse. On PowerShell:
   ```powershell
   $ACCOUNT = (aws sts get-caller-identity --query Account --output text)
   $REGION  = "us-east-1"           # pick a Region where the services/models are enabled
   $BUCKET  = "genai-demo-$ACCOUNT" # globally-unique name you own
   ```
   On bash/zsh:
   ```bash
   ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
   REGION=us-east-1
   BUCKET=genai-demo-$ACCOUNT
   ```
4. Create the shared demo bucket (used by several notebooks):
   ```bash
   aws s3api create-bucket --bucket "$BUCKET" --region "$REGION" \
     --create-bucket-configuration LocationConstraint="$REGION"
   aws s3api put-public-access-block --bucket "$BUCKET" \
     --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicPolicy=true
   ```
   > In `us-east-1`, omit the `--create-bucket-configuration` flag.

Fill the resulting values into each notebook's configuration cell
(`<AWS_REGION>`, `<YOUR_BUCKET_NAME>`, role ARNs, etc.).

---

## What each notebook needs at a glance

| Notebook | AWS services | Roles/resources to create | Notebook-principal privileges |
| --- | --- | --- | --- |
| Module_2_Slides_8_9_10 (Data Quality) | S3, Glue crawler, Glue Data Quality, (optional) Comprehend, (optional) CloudWatch | Glue service role + bucket | S3 R/W on prefix, Glue full for demo, `iam:PassRole` on the Glue role |
| Module_2_Slide_12 (PII protection) | Lambda, Comprehend, KMS, S3 | Lambda execution role + bucket + KMS key | Lambda create/get/invoke/delete, `iam:PassRole`, `sts:GetCallerIdentity` |
| Module_2_Slide_13 (Data lineage) | S3 (optional upload only) | bucket | `s3:PutObject`, `s3:HeadObject`, `sts:GetCallerIdentity` |
| Module_3_Slide_12 (Hybrid search) | Bedrock Runtime (Titan embeddings) | model access enabled | `bedrock:InvokeModel` on the embedding model |
| Module_3_Slide_29 (Comprehend) | Comprehend | (optional) custom classifier + endpoint | `comprehend:DetectEntities`, `comprehend:ClassifyDocument` |
| Module_4_Slides_5_10 (Prompt Mgmt) | Bedrock Agent (Prompt Management), Bedrock Runtime | model access enabled | `bedrock:CreatePrompt/GetPrompt/ListPrompts/UpdatePrompt/CreatePromptVersion/DeletePrompt`, `bedrock:InvokeModel`/`Converse` |
| Module_4_slide_25 (HR flow) | Bedrock Flows + Knowledge Base | flow + knowledge base + flow service role | `bedrock:InvokeFlow`, `bedrock:GetFlow` |

The notebook principal is *you* (your SSO user or IAM user). The **service
roles** below are assumed by the AWS services themselves, not by you.

---

## 1. Glue role — Module 2 Slides 8-10 (Data Quality)

The Glue crawler and Data Quality evaluation run under a service role that can
read your bucket and use Glue.

```bash
# Trust policy: allow Glue to assume the role
cat > glue-trust.json <<'JSON'
{ "Version": "2012-10-17",
  "Statement": [{ "Effect": "Allow",
    "Principal": { "Service": "glue.amazonaws.com" },
    "Action": "sts:AssumeRole" }] }
JSON

aws iam create-role --role-name genai-demo-glue-role \
  --assume-role-policy-document file://glue-trust.json

# AWS-managed baseline for Glue
aws iam attach-role-policy --role-name genai-demo-glue-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole

# Allow the role to read the demo data in your bucket
cat > glue-s3.json <<JSON
{ "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow", "Action": ["s3:GetObject","s3:PutObject"],
      "Resource": "arn:aws:s3:::$BUCKET/product-feedback/*" },
    { "Effect": "Allow", "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::$BUCKET" }
  ] }
JSON

aws iam put-role-policy --role-name genai-demo-glue-role \
  --policy-name genai-demo-glue-s3 --policy-document file://glue-s3.json
```

Then in the notebook set:
`GLUE_ROLE_ARN = "arn:aws:iam::<AWS_ACCOUNT_ID>:role/genai-demo-glue-role"`.

**Your** (notebook principal) privileges for this demo: `s3:PutObject`,
`s3:GetObject`, `s3:ListBucket` on the bucket; Glue create/start/get for
crawlers, databases, tables, and Data Quality rulesets and runs; and
`iam:PassRole` for `genai-demo-glue-role`.

---

## 2. Lambda role — Module 2 Slide 12 (PII protection)

First create a customer-managed KMS key and capture its ARN:

```bash
KMS_KEY_ARN=$(aws kms create-key --description "genai PII demo key" \
  --query KeyMetadata.Arn --output text)
echo "$KMS_KEY_ARN"
```

Create the Lambda execution role:

```bash
cat > lambda-trust.json <<'JSON'
{ "Version": "2012-10-17",
  "Statement": [{ "Effect": "Allow",
    "Principal": { "Service": "lambda.amazonaws.com" },
    "Action": "sts:AssumeRole" }] }
JSON

aws iam create-role --role-name genai-demo-pii-lambda-role \
  --assume-role-policy-document file://lambda-trust.json

# CloudWatch Logs for the function
aws iam attach-role-policy --role-name genai-demo-pii-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Comprehend + KMS + S3 write for the six privacy actions
cat > lambda-inline.json <<JSON
{ "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow", "Action": "comprehend:DetectPiiEntities", "Resource": "*" },
    { "Effect": "Allow", "Action": ["kms:Encrypt","kms:GenerateDataKey"], "Resource": "$KMS_KEY_ARN" },
    { "Effect": "Allow", "Action": "s3:PutObject", "Resource": "arn:aws:s3:::$BUCKET/pii-demo/*" }
  ] }
JSON

aws iam put-role-policy --role-name genai-demo-pii-lambda-role \
  --policy-name genai-demo-pii-inline --policy-document file://lambda-inline.json
```

In the notebook set `LAMBDA_ROLE_ARN`, `VAULT_BUCKET`, and `KMS_KEY_ARN` to the
values above.

**Your** privileges for this demo: `lambda:CreateFunction`,
`lambda:GetFunction`, `lambda:InvokeFunction`, `lambda:DeleteFunction`,
`iam:PassRole` for `genai-demo-pii-lambda-role`, and `sts:GetCallerIdentity`.

---

## 3. Bedrock model access — Modules 3 and 4

Prompt Management, the Converse call, and Titan embeddings all need **model
access** enabled once per account/Region:

1. Amazon Bedrock console -> **Model access** -> **Manage model access**.
2. Enable the models you will use, for example Amazon Titan Text Embeddings V2
   (`amazon.titan-embed-text-v2:0`) and Amazon Nova Lite (`amazon.nova-lite-v1:0`).
3. Wait until each shows **Access granted**.

Notebook-principal privileges:

- Module 3 Slide 12: `bedrock:InvokeModel` on the embedding model.
- Module 3 Slide 29: `comprehend:DetectEntities`, and
  `comprehend:ClassifyDocument` only if you demo a custom classifier endpoint.
- Module 4 Slides 5-10: `bedrock:CreatePrompt`, `bedrock:GetPrompt`,
  `bedrock:ListPrompts`, `bedrock:UpdatePrompt`, `bedrock:CreatePromptVersion`,
  `bedrock:DeletePrompt`, plus `bedrock:InvokeModel` / `bedrock:Converse` when
  invoking the versioned prompt.

---

## 4. Bedrock Flow + Knowledge Base — Module 4 Slide 25 (HR assistant)

This demo needs a flow you build in the console; there is no CLI one-liner.

1. Upload the sample HR documents to your bucket:
   ```bash
   aws s3 cp sample_data/hr_policies/ "s3://$BUCKET/hr-policies/" --recursive
   ```
2. Bedrock console -> **Knowledge bases** -> create one pointing at
   `s3://<YOUR_BUCKET_NAME>/hr-policies/`, then **Sync** the data source.
3. Bedrock console -> **Flows** -> create a flow with:
   - a **Flow input** node named `InputQuestion` (output name `document`),
   - a **Knowledge Base** node wired to the knowledge base above,
   - a **Flow output** node returning `document`.
4. Save, then note the **Flow ID**. The default test alias is `TSTALIASID`.

Notebook-principal privileges: `bedrock:InvokeFlow` and `bedrock:GetFlow`. The
**flow's service role** (configured when you create the flow) needs
`bedrock:InvokeModel` on the chosen model and `bedrock:Retrieve` on the
knowledge base.

---

## Cleanup

- Data Quality: run the notebook's cleanup cell (deletes crawler, ruleset,
  database/table, and the uploaded object).
- PII: the notebook deletes the Lambda function; delete the role, KMS key, and
  any vault/quarantine objects yourself.
- Prompt Management: set `DELETE_DEMO_RESOURCES = True` and rerun the cleanup cell.
- HR flow: delete the flow, knowledge base, and uploaded documents when done.
- Roles/keys you created here:
  ```bash
  aws iam delete-role-policy --role-name genai-demo-glue-role --policy-name genai-demo-glue-s3
  aws iam detach-role-policy --role-name genai-demo-glue-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole
  aws iam delete-role --role-name genai-demo-glue-role
  # repeat for genai-demo-pii-lambda-role; schedule KMS key deletion via aws kms schedule-key-deletion
  ```
