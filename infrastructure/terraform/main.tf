# NexaFi Infrastructure - AWS Multi-Region Setup
terraform {
  required_version = ">= 1.0"
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
  }
  
  backend "s3" {
    bucket         = "nexafi-terraform-state"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "nexafi-terraform-locks"
  }
}

# Primary region provider
provider "aws" {
  alias  = "primary"
  region = var.primary_region
  
  default_tags {
    tags = {
      Environment = var.environment
      Project     = "NexaFi"
      ManagedBy   = "Terraform"
      Compliance  = "Financial"
    }
  }
}

# Secondary region provider for DR
provider "aws" {
  alias  = "secondary"
  region = var.secondary_region
  
  default_tags {
    tags = {
      Environment = var.environment
      Project     = "NexaFi"
      ManagedBy   = "Terraform"
      Compliance  = "Financial"
      Purpose     = "DisasterRecovery"
    }
  }
}

# Variables
variable "environment" {
  description = "Environment name (prod, staging, dev)"
  type        = string
  default     = "prod"
}

variable "primary_region" {
  description = "Primary AWS region"
  type        = string
  default     = "us-east-1"
}

variable "secondary_region" {
  description = "Secondary AWS region for DR"
  type        = string
  default     = "us-west-2"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "nexafi-cluster"
}

variable "node_instance_types" {
  description = "EC2 instance types for EKS nodes"
  type        = list(string)
  default     = ["m5.large", "m5.xlarge"]
}

variable "min_nodes" {
  description = "Minimum number of nodes in the cluster"
  type        = number
  default     = 3
}

variable "max_nodes" {
  description = "Maximum number of nodes in the cluster"
  type        = number
  default     = 10
}

variable "desired_nodes" {
  description = "Desired number of nodes in the cluster"
  type        = number
  default     = 5
}

# Data sources
data "aws_availability_zones" "primary" {
  provider = aws.primary
  state    = "available"
}

data "aws_availability_zones" "secondary" {
  provider = aws.secondary
  state    = "available"
}

data "aws_caller_identity" "current" {}

# Local values
locals {
  cluster_name_primary   = "${var.cluster_name}-${var.primary_region}"
  cluster_name_secondary = "${var.cluster_name}-${var.secondary_region}"
  
  common_tags = {
    Environment = var.environment
    Project     = "NexaFi"
    ManagedBy   = "Terraform"
    Compliance  = "Financial"
  }
}

