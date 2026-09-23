# AWS Data Quality Demo Participant Notebook

Download `Module_2_Data_Quality_Demo_Participant.ipynb` and open it in VS Code with the Python and Jupyter extensions.

1. Run the first code cell. It defaults to a local-only run.
2. For the AWS path, edit the `PARTICIPANT INPUTS` block at the top.
3. Replace the S3 bucket and Glue service role placeholders, then set `RUN_AWS = True`.
4. Use an existing AWS CLI or SSO profile. Do not put access keys or secrets in the notebook.
5. Run the cleanup cell after the exercise to remove the resources created by the run.

The AWS path can incur charges. The Glue role must be trusted by AWS Glue and have access to the S3 prefix and Glue Data Quality. The notebook user also needs the required S3/Glue permissions and `iam:PassRole` for the role.
