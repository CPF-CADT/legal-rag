terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = "legal-rag"
      ManagedBy = "terraform"
    }
  }
}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }

  filter {
    name   = "availability-zone"
    values = [var.aws_availability_zone]
  }
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_security_group" "legal_rag" {
  name        = "legal-rag-ec2"
  description = "SSH access for the LegalRAG EC2 instance"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH administration"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
  }

  egress {
    description = "Outbound web and package/API access"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "legal_rag" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  availability_zone           = var.aws_availability_zone
  subnet_id                   = data.aws_subnets.default.ids[0]
  key_name                    = var.key_name
  vpc_security_group_ids      = [aws_security_group.legal_rag.id]
  associate_public_ip_address = true

  user_data = templatefile("${path.module}/setup.sh", {
    app_root    = var.app_root
    app_user    = var.app_user
    data_device = var.data_device
    mount_point = var.mount_point
  })

  user_data_replace_on_change = true

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 30
    encrypted             = true
    delete_on_termination = true
  }

  tags = {
    Name = "legal-rag"
  }
}

resource "aws_ebs_volume" "data" {
  availability_zone = aws_instance.legal_rag.availability_zone
  size              = 40
  type              = "gp3"
  encrypted         = true

  tags = {
    Name = "legal-rag-data"
  }
}

resource "aws_volume_attachment" "data" {
  device_name = var.data_device
  volume_id   = aws_ebs_volume.data.id
  instance_id = aws_instance.legal_rag.id
}
