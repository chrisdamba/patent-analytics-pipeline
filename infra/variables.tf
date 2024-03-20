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
