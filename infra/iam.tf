
resource "aws_iam_role" "mwaa_execution_role" {
  name               = "mwaa-${var.environment_name}-execution-role"
  assume_role_policy = data.aws_iam_policy_document.mwaa_assume.json
}

resource "aws_iam_role_policy" "mwaa_execution_policy" {
  name   = "mwaa-${var.environment_name}-execution-policy"
  policy = data.aws_iam_policy_document.mwaa_iam.json
  role   = aws_iam_role.mwaa_execution_role.id
}
