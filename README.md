# Advanced Generative AI Development on AWS — demo notebooks

Hands-on classroom notebooks for the *Advanced Generative AI Development on AWS*
course. Every notebook runs **offline by default** so you can explore the logic
without an AWS account, then switch on a guarded AWS path when you are ready.

## How the notebooks are designed

- **Offline first.** Each notebook has a switch (`RUN_AWS`, `USE_BEDROCK`, or
  `UPLOAD_TO_S3`) that defaults to the safe, local mode. Local cells use only
  the Python standard library (plus `matplotlib` for one optional chart).
- **Bring your own account.** All AWS identifiers are placeholders:
  `<AWS_ACCOUNT_ID>`, `<AWS_REGION>`, `<YOUR_BUCKET_NAME>`, `<YOUR_KMS_KEY_ID>`,
  role-name and flow-id placeholders. Fill them into the configuration cell,
  flip the switch to `True`, and the notebook works on your laptop.
- **No secrets in the notebook.** Credentials come from your AWS profile or SSO
  session, never from cells.

## Quick start

```bash
python -m venv .venv
# Windows PowerShell:  .venv\Scripts\Activate.ps1
# bash/zsh:            source .venv/bin/activate
python -m pip install -r requirements.txt
```

Open any notebook in VS Code or Jupyter, select the `.venv` kernel, and run the
cells top to bottom. They run offline as-is.

To use the AWS paths, first follow [`setup/create_roles.md`](setup/create_roles.md)
to create the roles and resources, then fill in the configuration cell and set
the notebook's switch to `True`.

## Notebooks

| Notebook | Topic | AWS services (optional path) |
| --- | --- | --- |
| `Module_2_Slides_8_9_10_Data_Quality_Demo_VS_Code.ipynb` | Data quality with Glue Data Quality (DQDL) and record-level routing | S3, Glue, Comprehend, CloudWatch |
| `Module_2_Slide_12_PII_Protection_Lambda_Comprehend_Demo.ipynb` | PII detection and six privacy actions | Lambda, Comprehend, KMS, S3 |
| `Module_2_Slide_13_Data_Lineage_Source_to_Consumption_Demo.ipynb` | Source-to-consumption data lineage | S3 (optional) |
| `Module_3_Slide_12_Hybrid_vs_Semantic_Search_Demo.ipynb` | Keyword vs semantic vs hybrid search | Bedrock (Titan embeddings) |
| `Module_3_Slide_29_Comprehend_Entities_and_Custom_Classification.ipynb` | Entity detection and custom classification | Comprehend |
| `Module_4_Slides_5_to_10_Bedrock_Prompt_Management_Demo.ipynb` | Bedrock Prompt Management: templates, variables, versions | Bedrock Agent + Runtime |
| `Module_4_slide_25_test_hr_assistant_flow.ipynb` | Calling a Bedrock Flow (HR assistant) | Bedrock Flows + Knowledge Base |

## Sample data

- `sample_data/product_feedback.csv` — feedback rows for the data-quality demo.
- `sample_data/policies_raw.csv` — source rows for the lineage demo.
- `sample_data/hr_policies/` — **synthetic** HR policy documents for the HR
  assistant knowledge base. These are made-up examples for teaching, not real
  policies. Supply your own documents for a realistic knowledge base.

## Costs and cleanup

The AWS paths create billable resources. Each notebook has a cleanup cell or a
cleanup section in `setup/create_roles.md`. Delete resources after class.

## Verifying the notebooks

`setup/verify_local.py` executes the offline path of every notebook and reports
whether each one runs cleanly without AWS:

```bash
python setup/verify_local.py
```
