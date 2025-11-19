# Enhanced Terraform configuration for NexaFi infrastructure
terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }

  backend "s3" {
    bucket         = "nexafi-terraform-state"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "nexafi-terraform-locks"

    # Enhanced security for state file
    kms_key_id = "alias/nexafi-terraform-state"

    # Versioning and lifecycle
    versioning = true
  }
}

# Provider configurations
provider "aws" {
  region = var.primary_region

  default_tags {
    tags = {
      Project             = "NexaFi"
      Environment         = var.environment
      ManagedBy          = "Terraform"
      SecurityCompliance = "PCI-DSS,SOC2,GDPR"
      DataClassification = "Confidential"
      BackupRequired     = "true"
      MonitoringEnabled  = "true"
    }
  }
}

provider "aws" {
  alias  = "secondary"
  region = var.secondary_region

  default_tags {
    tags = {
      Project             = "NexaFi"
      Environment         = var.environment
      ManagedBy          = "Terraform"
      SecurityCompliance = "PCI-DSS,SOC2,GDPR"
      DataClassification = "Confidential"
      BackupRequired     = "true"
      MonitoringEnabled  = "true"
      DisasterRecovery   = "true"
    }
  }
}

provider "kubernetes" {
  host                   = module.eks_primary.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks_primary.cluster_certificate_authority_data)

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", module.eks_primary.cluster_name]
  }
}

provider "helm" {
  kubernetes {
    host                   = module.eks_primary.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks_primary.cluster_certificate_authority_data)

    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", module.eks_primary.cluster_name]
    }
  }
}

# Local values for common configurations
locals {
  name_prefix = "nexafi-${var.environment}"

  common_tags = {
    Project             = "NexaFi"
    Environment         = var.environment
    ManagedBy          = "Terraform"
    SecurityCompliance = "PCI-DSS,SOC2,GDPR"
    DataClassification = "Confidential"
  }

  # Financial industry compliance requirements
  compliance_tags = {
    PCI_DSS_Scope      = "true"
    SOC2_Type2         = "true"
    GDPR_Applicable    = "true"
    SOX_Applicable     = "true"
    GLBA_Applicable    = "true"
    FFIEC_Applicable   = "true"
  }

  # Security configuration
  security_config = {
    enable_encryption_at_rest     = true
    enable_encryption_in_transit  = true
    enable_network_segmentation   = true
    enable_audit_logging         = true
    enable_vulnerability_scanning = true
    enable_intrusion_detection   = true
    enable_data_loss_prevention  = true
  }

  # Monitoring and alerting
  monitoring_config = {
    enable_cloudtrail           = true
    enable_config_rules         = true
    enable_guardduty           = true
    enable_security_hub        = true
    enable_inspector           = true
    enable_macie               = true
    enable_cloudwatch_insights = true
  }

  # Backup and disaster recovery
  backup_config = {
    backup_retention_days       = 2555  # 7 years for financial compliance
    cross_region_backup        = true
    point_in_time_recovery     = true
    automated_backup_testing   = true
    disaster_recovery_testing  = true
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}

# Random password for various services
resource "random_password" "master_password" {
  length  = 32
  special = true
}

# KMS keys for encryption
resource "aws_kms_key" "nexafi_primary" {
  description             = "NexaFi primary encryption key"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow EKS Service"
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-primary-key"
    Type = "encryption"
  })
}

resource "aws_kms_alias" "nexafi_primary" {
  name          = "alias/${local.name_prefix}-primary"
  target_key_id = aws_kms_key.nexafi_primary.key_id
}

# CloudTrail for audit logging
resource "aws_cloudtrail" "nexafi_audit" {
  name           = "${local.name_prefix}-audit-trail"
  s3_bucket_name = aws_s3_bucket.audit_logs.bucket

  include_global_service_events = true
  is_multi_region_trail        = true
  enable_logging               = true

  # Enhanced logging for financial compliance
  enable_log_file_validation = true

  # KMS encryption for audit logs
  kms_key_id = aws_kms_key.nexafi_primary.arn

  event_selector {
    read_write_type                 = "All"
    include_management_events       = true
    exclude_management_event_sources = []

    data_resource {
      type   = "AWS::S3::Object"
      values = ["arn:aws:s3:::${aws_s3_bucket.audit_logs.bucket}/*"]
    }

    data_resource {
      type   = "AWS::KMS::Key"
      values = ["*"]
    }
  }

  insight_selector {
    insight_type = "ApiCallRateInsight"
  }

  tags = merge(local.common_tags, local.compliance_tags, {
    Name = "${local.name_prefix}-audit-trail"
    Type = "audit"
  })
}

# S3 bucket for audit logs
resource "aws_s3_bucket" "audit_logs" {
  bucket        = "${local.name_prefix}-audit-logs-${random_id.bucket_suffix.hex}"
  force_destroy = false

  tags = merge(local.common_tags, local.compliance_tags, {
    Name = "${local.name_prefix}-audit-logs"
    Type = "audit"
  })
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket_versioning" "audit_logs" {
  bucket = aws_s3_bucket.audit_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_encryption" "audit_logs" {
  bucket = aws_s3_bucket.audit_logs.id

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        kms_master_key_id = aws_kms_key.nexafi_primary.arn
        sse_algorithm     = "aws:kms"
      }
      bucket_key_enabled = true
    }
  }
}

resource "aws_s3_bucket_public_access_block" "audit_logs" {
  bucket = aws_s3_bucket.audit_logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "audit_logs" {
  bucket = aws_s3_bucket.audit_logs.id

  rule {
    id     = "audit_log_lifecycle"
    status = "Enabled"

    # Transition to IA after 30 days
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    # Transition to Glacier after 90 days
    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    # Transition to Deep Archive after 365 days
    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }

    # Retain for 7 years (financial compliance)
    expiration {
      days = 2555
    }

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}

# GuardDuty for threat detection
resource "aws_guardduty_detector" "nexafi" {
  enable = true

  datasources {
    s3_logs {
      enable = true
    }
    kubernetes {
      audit_logs {
        enable = true
      }
    }
    malware_protection {
      scan_ec2_instance_with_findings {
        ebs_volumes {
          enable = true
        }
      }
    }
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-guardduty"
    Type = "security"
  })
}

# Security Hub for centralized security findings
resource "aws_securityhub_account" "nexafi" {
  enable_default_standards = true
}

# Config for compliance monitoring
resource "aws_config_configuration_recorder" "nexafi" {
  name     = "${local.name_prefix}-config-recorder"
  role_arn = aws_iam_role.config.arn

  recording_group {
    all_supported                 = true
    include_global_resource_types = true
  }
}

resource "aws_config_delivery_channel" "nexafi" {
  name           = "${local.name_prefix}-config-delivery"
  s3_bucket_name = aws_s3_bucket.config.bucket
}

resource "aws_s3_bucket" "config" {
  bucket        = "${local.name_prefix}-config-${random_id.bucket_suffix.hex}"
  force_destroy = false

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-config"
    Type = "compliance"
  })
}

# IAM role for Config
resource "aws_iam_role" "config" {
  name = "${local.name_prefix}-config-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-config-role"
    Type = "iam"
  })
}

resource "aws_iam_role_policy_attachment" "config" {
  role       = aws_iam_role.config.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/ConfigRole"
}

# Variables
variable "environment" {
  description = "Environment name (e.g., prod, staging, dev)"
  type        = string
  default     = "prod"
}

variable "primary_region" {
  description = "Primary AWS region"
  type        = string
  default     = "us-west-2"
}

variable "secondary_region" {
  description = "Secondary AWS region for disaster recovery"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr_primary" {
  description = "CIDR block for primary VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "vpc_cidr_secondary" {
  description = "CIDR block for secondary VPC"
  type        = string
  default     = "10.1.0.0/16"
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets"
  type        = bool
  default     = true
}

variable "enable_vpn_gateway" {
  description = "Enable VPN Gateway"
  type        = bool
  default     = false
}

variable "eks_cluster_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.27"
}

variable "node_group_instance_types" {
  description = "Instance types for EKS node groups"
  type        = list(string)
  default     = ["m5.large", "m5.xlarge"]
}

variable "financial_node_group_instance_types" {
  description = "Instance types for financial services node group"
  type        = list(string)
  default     = ["c5.xlarge", "c5.2xlarge"]
}

# Outputs
output "primary_vpc_id" {
  description = "ID of the primary VPC"
  value       = module.vpc_primary.vpc_id
}

output "secondary_vpc_id" {
  description = "ID of the secondary VPC"
  value       = module.vpc_secondary.vpc_id
}

output "primary_eks_cluster_id" {
  description = "ID of the primary EKS cluster"
  value       = module.eks_primary.cluster_id
}

output "secondary_eks_cluster_id" {
  description = "ID of the secondary EKS cluster"
  value       = module.eks_secondary.cluster_id
}

output "primary_eks_cluster_endpoint" {
  description = "Endpoint of the primary EKS cluster"
  value       = module.eks_primary.cluster_endpoint
}

output "kms_key_id" {
  description = "ID of the primary KMS key"
  value       = aws_kms_key.nexafi_primary.key_id
}

output "cloudtrail_arn" {
  description = "ARN of the CloudTrail"
  value       = aws_cloudtrail.nexafi_audit.arn
}

output "audit_logs_bucket" {
  description = "Name of the audit logs S3 bucket"
  value       = aws_s3_bucket.audit_logs.bucket
}
