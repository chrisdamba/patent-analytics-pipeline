resource "aws_key_pair" "patent_key" {
  key_name   = "patent_key"
  public_key = file(var.public_key_path)
}

resource "aws_kms_key" "patent_kms_key" {
  description             = "KMS key 1"
  deletion_window_in_days = 10
}