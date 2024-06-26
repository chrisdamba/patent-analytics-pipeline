data "aws_ami" "server_ami" {
  most_recent = true
  owners      = ["099720109477"]
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

data "aws_iam_policy_document" "mwaa_assume" {
  version = "2012-10-17"
  statement {
    effect = "Allow"
    principals {
      identifiers = [
        "airflow-env.amazonaws.com",
        "airflow.amazonaws.com"
      ]
      type = "Service"
    }
    actions = [
      "sts:AssumeRole"
    ]
  }
}

data "aws_iam_policy_document" "mwaa_base" {
  version = "2012-10-17"
  statement {
    effect = "Allow"
    actions = [
      "airflow:PublishMetrics"
    ]
    resources = [
      "arn:aws:airflow:${var.region}:${var.account_id}:environment/${var.environment_name}"
    ]
  }
  statement {
    effect  = "Deny"
    actions = ["s3:ListAllMyBuckets"]
    resources = [
      aws_s3_bucket.mwaa_dags.arn,
      "${aws_s3_bucket.mwaa_dags.arn}/*",
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject*",
      "s3:GetBucket*",
      "s3:List*"
    ]
    resources = [
      aws_s3_bucket.mwaa_dags.arn,
      "${aws_s3_bucket.mwaa_dags.arn}/*",
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "s3:GetAccountPublicAccessBlock"
    ]
    resources = ["*"]
  }
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:CreateLogGroup",
      "logs:PutLogEvents",
      "logs:GetLogEvents",
      "logs:GetLogRecord",
      "logs:GetLogGroupFields",
      "logs:GetQueryResults"
    ]
    resources = [
      "arn:aws:logs:${var.region}:${var.account_id}:log-group:airflow-${var.environment_name}-*"
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "logs:DescribeLogGroups"
    ]
    resources = [
      "*"
    ]
  }
  statement {

    effect = "Allow"
    actions = [
      "cloudwatch:PutMetricData"
    ]
    resources = [
      "*"
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "sqs:ChangeMessageVisibility",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
      "sqs:GetQueueUrl",
      "sqs:ReceiveMessage",
      "sqs:SendMessage"
    ]
    resources = [
      "arn:aws:sqs:${var.region}:*:airflow-celery-*"
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "kms:Decrypt",
      "kms:DescribeKey",
      "kms:GenerateDataKey*",
      "kms:Encrypt"
    ]
    resources     = [aws_kms_key.patent_kms_key.arn]
    not_resources = []
    condition {
      test = "StringLike"
      values = var.kms_key_arn != null ? [
        "sqs.${var.region}.amazonaws.com",
        "s3.${var.region}.amazonaws.com"
        ] : [
        "sqs.${var.region}.amazonaws.com"
      ]
      variable = "kms:ViaService"
    }
  }
}

data "aws_iam_policy_document" "mwaa_iam" {
  source_policy_documents = [
    data.aws_iam_policy_document.mwaa_base.json,
    var.additional_execution_role_policy_document_json
  ]
}

data "aws_iam_policy_document" "snowflake_patent_grant_assume" {
  version = "2012-10-17"
  statement {
    effect = "Allow"
    principals {
      identifiers = [
        "s3.amazonaws.com"
      ]
      type = "Service"
    }
    actions = [
      "sts:AssumeRole"
    ]
  }
}

data "aws_iam_policy_document" "snowflake_patent_grant_base" {
  version = "2012-10-17"
  statement {
    effect = "Allow"
    actions = [
      "s3:ListBucket",
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject"
    ]
    resources = [
      "arn:aws:s3:::${var.raw_patent_data_bucket_name}",
      "arn:aws:s3:::${var.raw_patent_data_bucket_name}/*"
    ]
  }
}

data "aws_iam_policy_document" "snowflake_patent_grant_iam" {
  source_policy_documents = [
    data.aws_iam_policy_document.snowflake_patent_grant_base.json,
    var.additional_execution_role_policy_document_json
  ]
}