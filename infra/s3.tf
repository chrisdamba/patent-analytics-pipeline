resource "aws_s3_bucket" "raw_patent_data" {
  bucket = var.raw_patent_data_bucket_name

  tags = {
    Name        = "Patent Analytics S3 Bucket for Raw Data from Snowflake"
    Environment = "Dev"
  }
}

resource "aws_s3_bucket" "mwaa_dags" {
  bucket = var.mwaa_source_bucket_name

  tags = {
    Name        = "AWS Managed Workflows for Apache Airflow DAGs Bucket"
    Environment = "Dev"
    Purpose     = "MWAA DAGs and Config"
  }
}


resource "aws_s3_bucket_versioning" "mwaa_dags_versioning" {
  bucket = aws_s3_bucket.mwaa_dags.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "mwaa_dags_cleanup" {
  bucket = aws_s3_bucket.mwaa_dags.id

  rule {
    id = "rule-1"

    expiration {
      days = 90
    }

    status = "Enabled"
  }
}