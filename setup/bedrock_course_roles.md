# Bedrock classroom learner role

This guide prepares AWS access for the seven learner notebooks under `notebooks/`. Six notebooks can make optional AWS calls; the RAGAS dataset notebook is local-only and needs no AWS permissions.

## Role and sign-in

Create or assign one learner execution role, such as `GenAILearnerNotebookRole`, in the class AWS account. An AWS administrator must configure its trust relationship for the actual notebook runtime or assign it through IAM Identity Center. The trust principal is environment-specific, so do not copy a generic trust policy into production. Students should not receive IAM role-creation, policy-attachment, or administrator permissions.

Recommended student access is an AWS CLI named profile backed by IAM Identity Center/SSO:

```powershell
aws configure sso --profile genai-student
aws sso login --profile genai-student
$env:AWS_PROFILE = "genai-student"
$env:AWS_REGION = "us-east-1"
```

The first AWS configuration cell in each AWS-capable learner notebook uses that profile/runtime credential chain by default. If the training environment explicitly provides temporary credentials instead, change `AWS_AUTH_METHOD` to `"keys"` in that cell. The notebook uses hidden prompts for the access key, secret, and optional session token; values are only held in the active kernel. Never use long-lived IAM user keys or commit credentials.

## Learner permission policy

Attach a customized version of this policy to the learner role. Replace `<REGION>` and `<AWS_ACCOUNT_ID>` with the class values, and replace `<YOUR_BUCKET_NAME>/<DOCUMENT_PREFIX>` only if using the optional S3 document example in the sentiment lab. Remove model ARNs not used in class and add the precise inference-profile/model ARNs enabled in the account. Cross-Region inference profiles may also require their backing foundation-model ARNs in the destination Regions.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DiscoverModels",
      "Effect": "Allow",
      "Action": "bedrock:ListFoundationModels",
      "Resource": "*"
    },
    {
      "Sid": "InvokeClassModels",
      "Effect": "Allow",
      "Action": "bedrock:InvokeModel",
      "Resource": [
        "arn:aws:bedrock:<REGION>::foundation-model/amazon.nova-lite-v1:0",
        "arn:aws:bedrock:<REGION>:<AWS_ACCOUNT_ID>:inference-profile/us.amazon.nova-lite-v1:0",
        "arn:aws:bedrock:<REGION>:<AWS_ACCOUNT_ID>:inference-profile/global.anthropic.claude-sonnet-4-6",
        "arn:aws:bedrock:<REGION>::foundation-model/amazon.titan-embed-text-v2:0"
      ]
    },
    {
      "Sid": "CreateClassGuardrails",
      "Effect": "Allow",
      "Action": ["bedrock:CreateGuardrail", "bedrock:CreateGuardrailVersion"],
      "Resource": "*"
    },
    {
      "Sid": "UseClassGuardrails",
      "Effect": "Allow",
      "Action": [
        "bedrock:GetGuardrail",
        "bedrock:DeleteGuardrail",
        "bedrock:ApplyGuardrail"
      ],
      "Resource": "arn:aws:bedrock:<REGION>:<AWS_ACCOUNT_ID>:guardrail/*"
    },
    {
      "Sid": "CreateClassTables",
      "Effect": "Allow",
      "Action": "dynamodb:CreateTable",
      "Resource": "*"
    },
    {
      "Sid": "UseClassTables",
      "Effect": "Allow",
      "Action": [
        "dynamodb:DescribeTable",
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:Query",
        "dynamodb:DeleteTable"
      ],
      "Resource": [
        "arn:aws:dynamodb:<REGION>:<AWS_ACCOUNT_ID>:table/bedrock-ebike-conversation-demo",
        "arn:aws:dynamodb:<REGION>:<AWS_ACCOUNT_ID>:table/EBikeSupportSessionTable"
      ]
    },
    {
      "Sid": "ReadOptionalClassDocuments",
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::<YOUR_BUCKET_NAME>/<DOCUMENT_PREFIX>/*"
    },
    {
      "Sid": "VerifyCallerIdentity",
      "Effect": "Allow",
      "Action": "sts:GetCallerIdentity",
      "Resource": "*"
    }
  ]
}
```

The S3 statement is optional and should be omitted if the class does not use the S3 document example. DynamoDB `CreateTable` uses `Resource: "*"` because the table does not exist yet; the remaining table actions are limited to the two lab table names. `bedrock:CreateGuardrail` may require wildcard resource scope; keep the role restricted to the classroom account and duration, and remove guardrail actions if that notebook section is not taught.

## Notebook mapping

| Learner notebook                                                 | AWS access used                                                                                                                         |
| ---------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `Amazon_Bedrock_End_to_End_EBike_Demo_Student.ipynb`             | Bedrock model invocation; create/read/write/query/delete its DynamoDB conversation table                                                |
| `MLDGAI_M09_Tools_Agents_Trainer_Demo_Student.ipynb`             | Bedrock model invocation; Strands/MCP examples also need outbound internet for the AWS Documentation MCP server                         |
| `Module_08_Responsible_AI_Bedrock_Guardrails_Demo_Student.ipynb` | Bedrock model invocation and Guardrail create/version/get/apply/delete operations                                                       |
| `Module4_sentiment_Student.ipynb`                                | Bedrock model invocation; optional S3 document input requires read access to the learner's own object prefix                            |
| `Module6_OpenSource_Frameworks_Bedrock_Demo_Student.ipynb`       | Bedrock model invocation; create/read/write/query/delete its DynamoDB conversation table                                                |
| `Module_9_crewai-travel-research_Student.ipynb`                  | Bedrock model invocation and model discovery; optional live Serper search uses a separate `SERPER_API_KEY` and is not an AWS credential |
| `M7_ragas_ebike_evaluation_dataset_Student.ipynb`                | Local-only; no AWS role required                                                                                                        |

The CrewAI `Evidence-focused Travel Researcher` and `Practical Itinerary Planner` are application-level agent roles, not IAM roles. They are defined and used in their notebook. The class execution role only authorizes the notebook's AWS API calls.

## Cleanup

Run each notebook's cleanup section after class. Delete any remaining DynamoDB tables or Bedrock Guardrails created during the lab, and remove the temporary learner role/permission assignment according to the class account policy. Do not delete shared resources owned by another class.
