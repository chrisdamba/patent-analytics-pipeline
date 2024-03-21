resource "aws_mwaa_environment" "patent_analytics_airflow" {
  airflow_configuration_options = {
    "core.default_task_retries" = 16
    "core.parallelism"          = 1
  }

  dag_s3_path        = "dags/"
  execution_role_arn = aws_iam_role.mwaa_execution_role.arn
  name               = "patent_analytics_airflow"

  network_configuration {
    security_group_ids = [aws_security_group.patent_mwaa_sg.id, aws_security_group.patent_sg.id]
    subnet_ids         = aws_subnet.private[*].id
  }

  source_bucket_arn = aws_s3_bucket.mwaa_dags.arn
}