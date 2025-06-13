# EKS Cluster for Primary Region
module "eks_primary" {
  source = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"
  
  providers = {
    aws = aws.primary
  }

  cluster_name    = local.cluster_name_primary
  cluster_version = "1.27"

  vpc_id                         = module.vpc_primary.vpc_id
  subnet_ids                     = module.vpc_primary.private_subnets
  cluster_endpoint_public_access = true
  cluster_endpoint_private_access = true

  # Cluster encryption
  cluster_encryption_config = {
    provider_key_arn = aws_kms_key.eks_primary.arn
    resources        = ["secrets"]
  }

  # Cluster logging
  cluster_enabled_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  # EKS Managed Node Groups
  eks_managed_node_groups = {
    financial_services = {
      name = "financial-services"
      
      instance_types = var.node_instance_types
      capacity_type  = "ON_DEMAND"
      
      min_size     = var.min_nodes
      max_size     = var.max_nodes
      desired_size = var.desired_nodes

      # Use custom launch template for enhanced security
      use_custom_launch_template = true
      
      # EBS encryption
      block_device_mappings = {
        xvda = {
          device_name = "/dev/xvda"
          ebs = {
            volume_size           = 100
            volume_type           = "gp3"
            iops                  = 3000
            throughput            = 150
            encrypted             = true
            kms_key_id           = aws_kms_key.ebs_primary.arn
            delete_on_termination = true
          }
        }
      }

      # Security groups
      vpc_security_group_ids = [aws_security_group.eks_additional_primary.id]

      # Taints for financial workloads
      taints = {
        financial = {
          key    = "financial-workload"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      }

      labels = {
        Environment = var.environment
        NodeGroup   = "financial-services"
        Compliance  = "financial"
      }

      tags = merge(local.common_tags, {
        NodeGroup = "financial-services"
        Region    = var.primary_region
      })
    }

    compliance_monitoring = {
      name = "compliance-monitoring"
      
      instance_types = ["m5.large"]
      capacity_type  = "ON_DEMAND"
      
      min_size     = 2
      max_size     = 5
      desired_size = 2

      use_custom_launch_template = true
      
      block_device_mappings = {
        xvda = {
          device_name = "/dev/xvda"
          ebs = {
            volume_size           = 50
            volume_type           = "gp3"
            encrypted             = true
            kms_key_id           = aws_kms_key.ebs_primary.arn
            delete_on_termination = true
          }
        }
      }

      vpc_security_group_ids = [aws_security_group.eks_additional_primary.id]

      taints = {
        compliance = {
          key    = "compliance-workload"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      }

      labels = {
        Environment = var.environment
        NodeGroup   = "compliance-monitoring"
        Purpose     = "compliance"
      }

      tags = merge(local.common_tags, {
        NodeGroup = "compliance-monitoring"
        Region    = var.primary_region
      })
    }
  }

  # Fargate profiles for serverless workloads
  fargate_profiles = {
    audit_logs = {
      name = "audit-logs"
      selectors = [
        {
          namespace = "nexafi"
          labels = {
            tier = "audit"
          }
        }
      ]

      tags = merge(local.common_tags, {
        Profile = "audit-logs"
        Region  = var.primary_region
      })
    }
  }

  # OIDC Identity provider
  cluster_identity_providers = {
    sts = {
      client_id = "sts.amazonaws.com"
    }
  }

  tags = merge(local.common_tags, {
    Region = var.primary_region
    Type   = "Primary"
  })
}

# EKS Cluster for Secondary Region (DR)
module "eks_secondary" {
  source = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"
  
  providers = {
    aws = aws.secondary
  }

  cluster_name    = local.cluster_name_secondary
  cluster_version = "1.27"

  vpc_id                         = module.vpc_secondary.vpc_id
  subnet_ids                     = module.vpc_secondary.private_subnets
  cluster_endpoint_public_access = true
  cluster_endpoint_private_access = true

  # Cluster encryption
  cluster_encryption_config = {
    provider_key_arn = aws_kms_key.eks_secondary.arn
    resources        = ["secrets"]
  }

  # Cluster logging
  cluster_enabled_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  # Minimal node group for DR (can be scaled up during failover)
  eks_managed_node_groups = {
    dr_standby = {
      name = "dr-standby"
      
      instance_types = ["m5.large"]
      capacity_type  = "ON_DEMAND"
      
      min_size     = 1
      max_size     = var.max_nodes
      desired_size = 1

      use_custom_launch_template = true
      
      block_device_mappings = {
        xvda = {
          device_name = "/dev/xvda"
          ebs = {
            volume_size           = 100
            volume_type           = "gp3"
            encrypted             = true
            kms_key_id           = aws_kms_key.ebs_secondary.arn
            delete_on_termination = true
          }
        }
      }

      vpc_security_group_ids = [aws_security_group.eks_additional_secondary.id]

      labels = {
        Environment = var.environment
        NodeGroup   = "dr-standby"
        Purpose     = "disaster-recovery"
      }

      tags = merge(local.common_tags, {
        NodeGroup = "dr-standby"
        Region    = var.secondary_region
        Purpose   = "DisasterRecovery"
      })
    }
  }

  tags = merge(local.common_tags, {
    Region  = var.secondary_region
    Type    = "Secondary"
    Purpose = "DisasterRecovery"
  })
}

# Additional security groups for enhanced security
resource "aws_security_group" "eks_additional_primary" {
  provider    = aws.primary
  name_prefix = "${local.cluster_name_primary}-additional"
  vpc_id      = module.vpc_primary.vpc_id

  # Financial compliance requirements
  ingress {
    description = "HTTPS from VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [module.vpc_primary.vpc_cidr_block]
  }

  ingress {
    description = "Secure communication between nodes"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    self        = true
  }

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name   = "${local.cluster_name_primary}-additional-sg"
    Region = var.primary_region
  })
}

resource "aws_security_group" "eks_additional_secondary" {
  provider    = aws.secondary
  name_prefix = "${local.cluster_name_secondary}-additional"
  vpc_id      = module.vpc_secondary.vpc_id

  ingress {
    description = "HTTPS from VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [module.vpc_secondary.vpc_cidr_block]
  }

  ingress {
    description = "Secure communication between nodes"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    self        = true
  }

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name    = "${local.cluster_name_secondary}-additional-sg"
    Region  = var.secondary_region
    Purpose = "DisasterRecovery"
  })
}

