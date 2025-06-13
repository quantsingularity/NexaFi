# KMS Keys for encryption
resource "aws_kms_key" "eks_primary" {
  provider                = aws.primary
  description             = "EKS Secret Encryption Key - Primary Region"
  deletion_window_in_days = 7
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
    Name   = "nexafi-eks-encryption-primary"
    Region = var.primary_region
  })
}

resource "aws_kms_alias" "eks_primary" {
  provider      = aws.primary
  name          = "alias/nexafi-eks-primary"
  target_key_id = aws_kms_key.eks_primary.key_id
}

resource "aws_kms_key" "eks_secondary" {
  provider                = aws.secondary
  description             = "EKS Secret Encryption Key - Secondary Region"
  deletion_window_in_days = 7
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
    Name    = "nexafi-eks-encryption-secondary"
    Region  = var.secondary_region
    Purpose = "DisasterRecovery"
  })
}

resource "aws_kms_alias" "eks_secondary" {
  provider      = aws.secondary
  name          = "alias/nexafi-eks-secondary"
  target_key_id = aws_kms_key.eks_secondary.key_id
}

# EBS encryption keys
resource "aws_kms_key" "ebs_primary" {
  provider                = aws.primary
  description             = "EBS Encryption Key - Primary Region"
  deletion_window_in_days = 7
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
        Sid    = "Allow EC2 Service"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey",
          "kms:Encrypt",
          "kms:GenerateDataKey*",
          "kms:ReEncrypt*"
        ]
        Resource = "*"
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name   = "nexafi-ebs-encryption-primary"
    Region = var.primary_region
  })
}

resource "aws_kms_alias" "ebs_primary" {
  provider      = aws.primary
  name          = "alias/nexafi-ebs-primary"
  target_key_id = aws_kms_key.ebs_primary.key_id
}

resource "aws_kms_key" "ebs_secondary" {
  provider                = aws.secondary
  description             = "EBS Encryption Key - Secondary Region"
  deletion_window_in_days = 7
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
        Sid    = "Allow EC2 Service"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey",
          "kms:Encrypt",
          "kms:GenerateDataKey*",
          "kms:ReEncrypt*"
        ]
        Resource = "*"
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name    = "nexafi-ebs-encryption-secondary"
    Region  = var.secondary_region
    Purpose = "DisasterRecovery"
  })
}

resource "aws_kms_alias" "ebs_secondary" {
  provider      = aws.secondary
  name          = "alias/nexafi-ebs-secondary"
  target_key_id = aws_kms_key.ebs_secondary.key_id
}

# RDS encryption keys
resource "aws_kms_key" "rds_primary" {
  provider                = aws.primary
  description             = "RDS Encryption Key - Primary Region"
  deletion_window_in_days = 7
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
        Sid    = "Allow RDS Service"
        Effect = "Allow"
        Principal = {
          Service = "rds.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey",
          "kms:Encrypt",
          "kms:GenerateDataKey*",
          "kms:ReEncrypt*"
        ]
        Resource = "*"
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name   = "nexafi-rds-encryption-primary"
    Region = var.primary_region
  })
}

resource "aws_kms_alias" "rds_primary" {
  provider      = aws.primary
  name          = "alias/nexafi-rds-primary"
  target_key_id = aws_kms_key.rds_primary.key_id
}

resource "aws_kms_key" "rds_secondary" {
  provider                = aws.secondary
  description             = "RDS Encryption Key - Secondary Region"
  deletion_window_in_days = 7
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
        Sid    = "Allow RDS Service"
        Effect = "Allow"
        Principal = {
          Service = "rds.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey",
          "kms:Encrypt",
          "kms:GenerateDataKey*",
          "kms:ReEncrypt*"
        ]
        Resource = "*"
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name    = "nexafi-rds-encryption-secondary"
    Region  = var.secondary_region
    Purpose = "DisasterRecovery"
  })
}

resource "aws_kms_alias" "rds_secondary" {
  provider      = aws.secondary
  name          = "alias/nexafi-rds-secondary"
  target_key_id = aws_kms_key.rds_secondary.key_id
}

