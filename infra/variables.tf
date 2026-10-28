variable "aws_region" {
  description = "AWS region for the EC2 instance and EBS volume."
  type        = string
  default     = "ap-southeast-1"
}

variable "aws_availability_zone" {
  description = "Standard Singapore Availability Zone for EC2 and EBS."
  type        = string
  default     = "ap-southeast-1c"
}

variable "instance_type" {
  description = "EC2 instance type for sequential scraping and OCR."
  type        = string
  default     = "t3.small"
}

variable "key_name" {
  description = "Existing EC2 key pair name used for SSH access."
  type        = string
  default     = "rag"
}

variable "admin_cidr" {
  description = "CIDR allowed to SSH to the instance. Public SSH access is enabled."
  type        = string
  default     = "0.0.0.0/0"
}

variable "app_user" {
  description = "Linux user that owns the application files."
  type        = string
  default     = "ubuntu"
}

variable "app_root" {
  description = "Application installation directory on EC2."
  type        = string
  default     = "/opt/legal-rag"
}

variable "mount_point" {
  description = "Persistent EBS mount point."
  type        = string
  default     = "/mnt/legal-rag-data"
}

variable "data_device" {
  description = "Linux device name requested for the EBS attachment."
  type        = string
  default     = "/dev/sdf"
}
