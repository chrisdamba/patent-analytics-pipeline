# general information
variable "region" {
  type        = string
  description = "AWS Region where the environment and its resources will be created"
  default     = "eu-west-2"
}

variable "account_id" {
  type        = string
  description = "Account ID of the account in which MWAA will be started"
}

variable "environment_name" {
  type        = string
  description = "Name of the MWAA environment"
  default     = "dev"
}

variable "airflow_version" {
  description = "Airflow version to be used"
  type        = string
  default     = "2.0.2"
}

# networking
variable "my_ip" {
  description = "Your IP address"
  type        = string
}

variable "public_key_path" {
  description = "The path to your public key"
  type        = string
}

variable "bucket_name" {
  type        = string
  description = "Name of the bucket for raw data storage"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for the public subnets MWAA uses. Must be at least 2 if create_networking_config=true"
  type        = list(string)
  default     = ["10.16.1.0/24", "10.16.2.0/24", "10.16.3.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for the private subnets MWAA uses. Must be at least 2 if create_networking_config=true"
  type        = list(string)
  default     = ["10.16.101.0/24", "10.16.102.0/24", "10.16.103.0/24"]
}

variable "additional_associated_security_group_ids" {
  description = "Security group IDs of existing security groups that should be associated with the MWAA environment."
  type        = list(string)
  default     = []
}

# iam
variable "additional_execution_role_policy_document_json" {
  description = "Additional permissions to attach to the base mwaa execution role"
  type        = string
  default     = "{}"
}

variable "kms_key_arn" {
  description = "ARN of the KMS key to use for MWAA encryption"
  type        = string
  default     = null
}

# s3 configuration

variable "raw_patent_data_bucket_name" {
  type        = string
  description = "Name of the bucket in which DAGs, Plugin and Requirements are put"
}

variable "mwaa_source_bucket_name" {
  type        = string
  description = "Name of the bucket in which DAGs, Plugin and Requirements are put"
}

variable "mwaa_source_bucket_arn" {
  type        = string
  description = "ARN of the bucket in which DAGs, Plugin and Requirements are put"
}

variable "dag_s3_path" {
  description = "Relative path of the dags folder within the source bucket"
  type        = string
  default     = "dags/"
}

variable "plugins_s3_path" {
  type        = string
  description = "relative path of the plugins.zip within the source bucket"
  default     = null
}

variable "plugins_s3_object_version" {
  default = null
  type    = string
}

variable "requirements_s3_path" {
  type        = string
  description = "relative path of the requirements.txt (incl. filename) within the source bucket"
  default     = null
}

variable "requirements_s3_object_version" {
  default = null
  type    = string
}
variable "startup_script_s3_path" {
  type        = string
  description = "The relative path to the script hosted in your bucket. The script runs as your environment starts before starting the Apache Airflow process."
  default     = null
}

variable "startup_script_s3_object_version" {
  default = null
  type    = string
}

# airflow.cfg values
variable "airflow_configuration_options" {
  description = "additional configuration to overwrite airflows standard config"
  type        = map(string)
  default     = {}
}
