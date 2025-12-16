# Enhanced EKS configuration for NexaFi with financial industry security standards

# Primary EKS Cluster
module "eks_primary" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "${local.name_prefix}-primary"
  cluster_version = var.eks_cluster_version

  vpc_id                   = module.vpc_primary.vpc_id
  subnet_ids               = module.vpc_primary.private_subnets
  control_plane_subnet_ids = module.vpc_primary.intra_subnets

  # Enhanced security configuration
  cluster_endpoint_private_access      = true
  cluster_endpoint_public_access       = true
  cluster_endpoint_public_access_cidrs = ["0.0.0.0/0"] # Restrict in production

  # Encryption configuration
  cluster_encryption_config = {
    provider_key_arn = aws_kms_key.nexafi_primary.arn
    resources        = ["secrets"]
  }

  # Enhanced logging for compliance
  cluster_enabled_log_types = [
    "api",
    "audit",
    "authenticator",
    "controllerManager",
    "scheduler"
  ]

  cloudwatch_log_group_retention_in_days = 2555 # 7 years for financial compliance
  cloudwatch_log_group_kms_key_id        = aws_kms_key.nexafi_primary.arn

  # Cluster security group
  cluster_security_group_additional_rules = {
    ingress_nodes_443 = {
      description                = "Node groups to cluster API"
      protocol                   = "tcp"
      from_port                  = 443
      to_port                    = 443
      type                       = "ingress"
      source_node_security_group = true
    }

    # Financial services specific ports
    ingress_financial_8080 = {
      description = "Financial services communication"
      protocol    = "tcp"
      from_port   = 8080
      to_port     = 8090
      type        = "ingress"
      cidr_blocks = [var.vpc_cidr_primary]
    }

    # Vault communication
    ingress_vault = {
      description = "Vault communication"
      protocol    = "tcp"
      from_port   = 8200
      to_port     = 8201
      type        = "ingress"
      cidr_blocks = [var.vpc_cidr_primary]
    }
  }

  # Node security group
  node_security_group_additional_rules = {
    # Financial services inter-node communication
    ingress_self_all = {
      description = "Node to node all ports/protocols"
      protocol    = "-1"
      from_port   = 0
      to_port     = 0
      type        = "ingress"
      self        = true
    }

    # Database access
    egress_database = {
      description = "Database access"
      protocol    = "tcp"
      from_port   = 5432
      to_port     = 5432
      type        = "egress"
      cidr_blocks = module.vpc_primary.database_subnets_cidr_blocks
    }

    # Redis access
    egress_redis = {
      description = "Redis access"
      protocol    = "tcp"
      from_port   = 6379
      to_port     = 6379
      type        = "egress"
      cidr_blocks = [var.vpc_cidr_primary]
    }

    # HTTPS outbound for external APIs
    egress_https = {
      description = "HTTPS outbound"
      protocol    = "tcp"
      from_port   = 443
      to_port     = 443
      type        = "egress"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  # EKS Managed Node Groups
  eks_managed_node_groups = {
    # General purpose node group
    general = {
      name = "general"

      instance_types = var.node_group_instance_types
      capacity_type  = "ON_DEMAND"

      min_size     = 2
      max_size     = 10
      desired_size = 3

      # Enhanced security
      enable_bootstrap_user_data = true
      bootstrap_extra_args       = "--container-runtime containerd --kubelet-extra-args '--max-pods=110'"

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
            kms_key_id            = aws_kms_key.nexafi_primary.arn
            delete_on_termination = true
          }
        }
      }

      # Metadata service configuration
      metadata_options = {
        http_endpoint               = "enabled"
        http_tokens                 = "required"
        http_put_response_hop_limit = 2
        instance_metadata_tags      = "enabled"
      }

      # Taints and labels
      taints = {}
      labels = {
        Environment = var.environment
        NodeGroup   = "general"
        Purpose     = "general-workloads"
      }

      tags = merge(local.common_tags, {
        Name = "${local.name_prefix}-general-node-group"
        Type = "eks-node-group"
      })
    }

    # Financial services dedicated node group
    financial_services = {
      name = "financial-services"

      instance_types = var.financial_node_group_instance_types
      capacity_type  = "ON_DEMAND"

      min_size     = 3
      max_size     = 15
      desired_size = 5

      # Enhanced security for financial workloads
      enable_bootstrap_user_data = true
      bootstrap_extra_args       = "--container-runtime containerd --kubelet-extra-args '--max-pods=110 --kube-reserved=cpu=250m,memory=1Gi,ephemeral-storage=1Gi --system-reserved=cpu=250m,memory=0.2Gi,ephemeral-storage=1Gi'"

      use_custom_launch_template = true

      # Larger encrypted storage for financial data
      block_device_mappings = {
        xvda = {
          device_name = "/dev/xvda"
          ebs = {
            volume_size           = 200
            volume_type           = "gp3"
            iops                  = 4000
            throughput            = 250
            encrypted             = true
            kms_key_id            = aws_kms_key.nexafi_primary.arn
            delete_on_termination = true
          }
        }
      }

      metadata_options = {
        http_endpoint               = "enabled"
        http_tokens                 = "required"
        http_put_response_hop_limit = 1
        instance_metadata_tags      = "enabled"
      }

      # Taints to ensure only financial services run on these nodes
      taints = {
        financial = {
          key    = "financial-services"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      }

      labels = {
        Environment = var.environment
        NodeGroup   = "financial-services"
        Purpose     = "financial-workloads"
        Compliance  = "PCI-DSS"
        Tier        = "financial"
      }

      tags = merge(local.common_tags, local.compliance_tags, {
        Name = "${local.name_prefix}-financial-services-node-group"
        Type = "eks-node-group"
        Tier = "financial"
      })
    }

    # Compliance and monitoring node group
    compliance_monitoring = {
      name = "compliance-monitoring"

      instance_types = ["m5.large", "m5.xlarge"]
      capacity_type  = "ON_DEMAND"

      min_size     = 2
      max_size     = 8
      desired_size = 3

      enable_bootstrap_user_data = true
      bootstrap_extra_args       = "--container-runtime containerd --kubelet-extra-args '--max-pods=110'"

      use_custom_launch_template = true

      block_device_mappings = {
        xvda = {
          device_name = "/dev/xvda"
          ebs = {
            volume_size           = 150
            volume_type           = "gp3"
            iops                  = 3000
            throughput            = 200
            encrypted             = true
            kms_key_id            = aws_kms_key.nexafi_primary.arn
            delete_on_termination = true
          }
        }
      }

      metadata_options = {
        http_endpoint               = "enabled"
        http_tokens                 = "required"
        http_put_response_hop_limit = 2
        instance_metadata_tags      = "enabled"
      }

      taints = {
        compliance = {
          key    = "compliance-monitoring"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      }

      labels = {
        Environment = var.environment
        NodeGroup   = "compliance-monitoring"
        Purpose     = "compliance-workloads"
        Tier        = "compliance"
      }

      tags = merge(local.common_tags, local.compliance_tags, {
        Name = "${local.name_prefix}-compliance-monitoring-node-group"
        Type = "eks-node-group"
        Tier = "compliance"
      })
    }
  }

  # Fargate profiles for serverless workloads
  fargate_profiles = {
    # Audit logs fargate profile
    audit_logs = {
      name = "audit-logs"
      selectors = [
        {
          namespace = "compliance"
          labels = {
            fargate = "audit-logs"
          }
        }
      ]

      subnet_ids = module.vpc_primary.private_subnets

      tags = merge(local.common_tags, {
        Name = "${local.name_prefix}-audit-logs-fargate"
        Type = "fargate-profile"
      })
    }

    # Security services fargate profile
    security_services = {
      name = "security-services"
      selectors = [
        {
          namespace = "security"
          labels = {
            fargate = "security-services"
          }
        }
      ]

      subnet_ids = module.vpc_primary.intra_subnets

      tags = merge(local.common_tags, {
        Name = "${local.name_prefix}-security-services-fargate"
        Type = "fargate-profile"
      })
    }
  }

  # IRSA (IAM Roles for Service Accounts)
  enable_irsa = true

  # Cluster addons
  cluster_addons = {
    coredns = {
      most_recent = true
      configuration_values = jsonencode({
        computeType = "Fargate"
        resources = {
          limits = {
            cpu    = "0.25"
            memory = "256M"
          }
          requests = {
            cpu    = "0.25"
            memory = "256M"
          }
        }
      })
    }

    kube-proxy = {
      most_recent = true
    }

    vpc-cni = {
      most_recent = true
      configuration_values = jsonencode({
        env = {
          ENABLE_POD_ENI                    = "true"
          ENABLE_PREFIX_DELEGATION          = "true"
          POD_SECURITY_GROUP_ENFORCING_MODE = "standard"
        }
      })
    }

    aws-ebs-csi-driver = {
      most_recent              = true
      service_account_role_arn = module.ebs_csi_irsa_role.iam_role_arn
    }

    aws-efs-csi-driver = {
      most_recent              = true
      service_account_role_arn = module.efs_csi_irsa_role.iam_role_arn
    }
  }

  tags = merge(local.common_tags, local.compliance_tags, {
    Name   = "${local.name_prefix}-primary-eks"
    Type   = "eks-cluster"
    Region = var.primary_region
  })
}

# Secondary EKS Cluster for disaster recovery
module "eks_secondary" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  providers = {
    aws = aws.secondary
  }

  cluster_name    = "${local.name_prefix}-secondary"
  cluster_version = var.eks_cluster_version

  vpc_id                   = module.vpc_secondary.vpc_id
  subnet_ids               = module.vpc_secondary.private_subnets
  control_plane_subnet_ids = module.vpc_secondary.intra_subnets

  cluster_endpoint_private_access      = true
  cluster_endpoint_public_access       = true
  cluster_endpoint_public_access_cidrs = ["0.0.0.0/0"]

  # Same encryption and logging configuration as primary
  cluster_encryption_config = {
    provider_key_arn = aws_kms_key.nexafi_primary.arn
    resources        = ["secrets"]
  }

  cluster_enabled_log_types = [
    "api",
    "audit",
    "authenticator",
    "controllerManager",
    "scheduler"
  ]

  cloudwatch_log_group_retention_in_days = 2555

  # Minimal node group for disaster recovery standby
  eks_managed_node_groups = {
    dr_standby = {
      name = "dr-standby"

      instance_types = ["t3.medium"]
      capacity_type  = "SPOT"

      min_size     = 1
      max_size     = 10
      desired_size = 1

      use_custom_launch_template = true

      block_device_mappings = {
        xvda = {
          device_name = "/dev/xvda"
          ebs = {
            volume_size           = 50
            volume_type           = "gp3"
            encrypted             = true
            delete_on_termination = true
          }
        }
      }

      metadata_options = {
        http_endpoint               = "enabled"
        http_tokens                 = "required"
        http_put_response_hop_limit = 2
      }

      labels = {
        Environment = var.environment
        NodeGroup   = "dr-standby"
        Purpose     = "disaster-recovery"
      }

      tags = merge(local.common_tags, {
        Name    = "${local.name_prefix}-dr-standby-node-group"
        Type    = "eks-node-group"
        Purpose = "disaster-recovery"
      })
    }
  }

  enable_irsa = true

  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent = true
    }
  }

  tags = merge(local.common_tags, {
    Name    = "${local.name_prefix}-secondary-eks"
    Type    = "eks-cluster"
    Region  = var.secondary_region
    Purpose = "disaster-recovery"
  })
}

# IRSA roles for CSI drivers
module "ebs_csi_irsa_role" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.0"

  role_name             = "${local.name_prefix}-ebs-csi"
  attach_ebs_csi_policy = true

  oidc_providers = {
    ex = {
      provider_arn               = module.eks_primary.oidc_provider_arn
      namespace_service_accounts = ["kube-system:ebs-csi-controller-sa"]
    }
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ebs-csi-irsa"
    Type = "iam-role"
  })
}

module "efs_csi_irsa_role" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.0"

  role_name             = "${local.name_prefix}-efs-csi"
  attach_efs_csi_policy = true

  oidc_providers = {
    ex = {
      provider_arn               = module.eks_primary.oidc_provider_arn
      namespace_service_accounts = ["kube-system:efs-csi-controller-sa"]
    }
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-efs-csi-irsa"
    Type = "iam-role"
  })
}

# Load Balancer Controller IRSA
module "load_balancer_controller_irsa_role" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.0"

  role_name                              = "${local.name_prefix}-load-balancer-controller"
  attach_load_balancer_controller_policy = true

  oidc_providers = {
    ex = {
      provider_arn               = module.eks_primary.oidc_provider_arn
      namespace_service_accounts = ["kube-system:aws-load-balancer-controller"]
    }
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-load-balancer-controller-irsa"
    Type = "iam-role"
  })
}

# External DNS IRSA
module "external_dns_irsa_role" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.0"

  role_name                     = "${local.name_prefix}-external-dns"
  attach_external_dns_policy    = true
  external_dns_hosted_zone_arns = ["arn:aws:route53:::hostedzone/*"]

  oidc_providers = {
    ex = {
      provider_arn               = module.eks_primary.oidc_provider_arn
      namespace_service_accounts = ["kube-system:external-dns"]
    }
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-external-dns-irsa"
    Type = "iam-role"
  })
}

# Cluster Autoscaler IRSA
module "cluster_autoscaler_irsa_role" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.0"

  role_name                        = "${local.name_prefix}-cluster-autoscaler"
  attach_cluster_autoscaler_policy = true
  cluster_autoscaler_cluster_names = [module.eks_primary.cluster_name]

  oidc_providers = {
    ex = {
      provider_arn               = module.eks_primary.oidc_provider_arn
      namespace_service_accounts = ["kube-system:cluster-autoscaler"]
    }
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-cluster-autoscaler-irsa"
    Type = "iam-role"
  })
}

# EFS for shared storage
resource "aws_efs_file_system" "shared_storage" {
  creation_token                  = "${local.name_prefix}-shared-storage"
  performance_mode                = "generalPurpose"
  throughput_mode                 = "provisioned"
  provisioned_throughput_in_mibps = 100

  encrypted  = true
  kms_key_id = aws_kms_key.nexafi_primary.arn

  lifecycle_policy {
    transition_to_ia = "AFTER_30_DAYS"
  }

  lifecycle_policy {
    transition_to_primary_storage_class = "AFTER_1_ACCESS"
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-shared-storage"
    Type = "efs"
  })
}

# EFS mount targets
resource "aws_efs_mount_target" "shared_storage" {
  count = length(module.vpc_primary.private_subnets)

  file_system_id  = aws_efs_file_system.shared_storage.id
  subnet_id       = module.vpc_primary.private_subnets[count.index]
  security_groups = [aws_security_group.efs.id]
}

# Security group for EFS
resource "aws_security_group" "efs" {
  name_prefix = "${local.name_prefix}-efs-"
  vpc_id      = module.vpc_primary.vpc_id
  description = "Security group for EFS mount targets"

  ingress {
    from_port   = 2049
    to_port     = 2049
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr_primary]
    description = "NFS from VPC"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-efs-sg"
    Type = "security-group"
  })
}
