# Terraform Outputs

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