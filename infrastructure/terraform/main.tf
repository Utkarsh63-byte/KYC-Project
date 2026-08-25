terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  default = "ap-south-1"
}

variable "environment" {
  default = "production"
}

# KMS Key for PII & Document Encryption
resource "aws_kms_key" "kyc_kms" {
  description             = "KMS Key for Enterprise KYC Encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true
}

# S3 Bucket with Object Lock (WORM Compliance)
resource "aws_s3_bucket" "kyc_documents" {
  bucket        = "enterprise-kyc-documents-${var.environment}"
  force_destroy = false
}

resource "aws_s3_bucket_object_lock_configuration" "kyc_worm" {
  bucket = aws_s3_bucket.kyc_documents.id
  rule {
    default_retention {
      mode = "COMPLIANCE"
      days = 2555 # 7-Year Retention
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "s3_kms" {
  bucket = aws_s3_bucket.kyc_documents.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.kyc_kms.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

# RDS PostgreSQL Multi-AZ Database Instance
resource "aws_db_instance" "kyc_rds" {
  identifier             = "kyc-postgres-${var.environment}"
  allocated_storage      = 50
  max_allocated_storage  = 500
  engine                 = "postgres"
  engine_version         = "15.4"
  instance_class         = "db.r6g.xlarge"
  db_name                = "kyc_db"
  username               = "kyc_admin"
  password               = var.db_password
  multi_az               = true
  storage_encrypted      = true
  kms_key_id             = aws_kms_key.kyc_kms.arn
  skip_final_snapshot    = false
  deletion_protection    = true
}

variable "db_password" {
  type      = string
  sensitive = true
}

output "s3_bucket_name" {
  value = aws_s3_bucket.kyc_documents.id
}

output "rds_endpoint" {
  value = aws_db_instance.kyc_rds.endpoint
}
