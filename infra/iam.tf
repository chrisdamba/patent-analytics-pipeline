
resource "aws_iam_role" "mwaa_execution_role" {
  name               = "mwaa-${var.environment_name}-execution-role"
  assume_role_policy = data.aws_iam_policy_document.mwaa_assume.json
}

resource "aws_iam_role_policy" "mwaa_execution_policy" {
  name   = "mwaa-${var.environment_name}-execution-policy"
  policy = data.aws_iam_policy_document.mwaa_iam.json
  role   = aws_iam_role.mwaa_execution_role.id
}


resource "aws_iam_role" "snowflake_patent_grants_execution_role" {
  name               = "patent-s3-${var.environment_name}-execution-role"
  assume_role_policy = data.aws_iam_policy_document.snowflake_patent_grant_assume.json
}

resource "aws_iam_role_policy" "snowflake_patent_grants_execution_policy" {
  name   = "patent-s3-${var.environment_name}-execution-policy"
  policy = data.aws_iam_policy_document.snowflake_patent_grant_iam.json
  role   = aws_iam_role.snowflake_patent_grants_execution_role.id
}