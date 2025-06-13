# VPC Configuration for Primary Region
module "vpc_primary" {
  source = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
  
  providers = {
    aws = aws.primary
  }

  name = "${var.cluster_name}-vpc-${var.primary_region}"
  cidr = "10.0.0.0/16"

  azs             = slice(data.aws_availability_zones.primary.names, 0, 3)
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  database_subnets = ["10.0.201.0/24", "10.0.202.0/24", "10.0.203.0/24"]

  enable_nat_gateway     = true
  single_nat_gateway     = false
  enable_vpn_gateway     = false
  enable_dns_hostnames   = true
  enable_dns_support     = true

  # Enable VPC Flow Logs for security monitoring
  enable_flow_log                      = true
  create_flow_log_cloudwatch_iam_role  = true
  create_flow_log_cloudwatch_log_group = true

  # Subnet tagging for EKS
  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
    "kubernetes.io/cluster/${local.cluster_name_primary}" = "owned"
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = "1"
    "kubernetes.io/cluster/${local.cluster_name_primary}" = "owned"
  }

  database_subnet_tags = {
    "Purpose" = "Database"
    "Tier"    = "Data"
  }

  tags = merge(local.common_tags, {
    Region = var.primary_region
    Type   = "Primary"
  })
}

# VPC Configuration for Secondary Region (DR)
module "vpc_secondary" {
  source = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
  
  providers = {
    aws = aws.secondary
  }

  name = "${var.cluster_name}-vpc-${var.secondary_region}"
  cidr = "10.1.0.0/16"

  azs             = slice(data.aws_availability_zones.secondary.names, 0, 3)
  private_subnets = ["10.1.1.0/24", "10.1.2.0/24", "10.1.3.0/24"]
  public_subnets  = ["10.1.101.0/24", "10.1.102.0/24", "10.1.103.0/24"]
  database_subnets = ["10.1.201.0/24", "10.1.202.0/24", "10.1.203.0/24"]

  enable_nat_gateway     = true
  single_nat_gateway     = false
  enable_vpn_gateway     = false
  enable_dns_hostnames   = true
  enable_dns_support     = true

  # Enable VPC Flow Logs for security monitoring
  enable_flow_log                      = true
  create_flow_log_cloudwatch_iam_role  = true
  create_flow_log_cloudwatch_log_group = true

  # Subnet tagging for EKS
  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
    "kubernetes.io/cluster/${local.cluster_name_secondary}" = "owned"
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = "1"
    "kubernetes.io/cluster/${local.cluster_name_secondary}" = "owned"
  }

  database_subnet_tags = {
    "Purpose" = "Database"
    "Tier"    = "Data"
  }

  tags = merge(local.common_tags, {
    Region = var.secondary_region
    Type   = "Secondary"
    Purpose = "DisasterRecovery"
  })
}

# VPC Peering between regions for cross-region communication
resource "aws_vpc_peering_connection" "primary_to_secondary" {
  provider    = aws.primary
  vpc_id      = module.vpc_primary.vpc_id
  peer_vpc_id = module.vpc_secondary.vpc_id
  peer_region = var.secondary_region
  auto_accept = false

  tags = merge(local.common_tags, {
    Name = "nexafi-vpc-peering-primary-to-secondary"
  })
}

resource "aws_vpc_peering_connection_accepter" "secondary" {
  provider                  = aws.secondary
  vpc_peering_connection_id = aws_vpc_peering_connection.primary_to_secondary.id
  auto_accept               = true

  tags = merge(local.common_tags, {
    Name = "nexafi-vpc-peering-accepter-secondary"
  })
}

# Route table entries for VPC peering
resource "aws_route" "primary_to_secondary" {
  provider                  = aws.primary
  count                     = length(module.vpc_primary.private_route_table_ids)
  route_table_id            = module.vpc_primary.private_route_table_ids[count.index]
  destination_cidr_block    = module.vpc_secondary.vpc_cidr_block
  vpc_peering_connection_id = aws_vpc_peering_connection.primary_to_secondary.id
}

resource "aws_route" "secondary_to_primary" {
  provider                  = aws.secondary
  count                     = length(module.vpc_secondary.private_route_table_ids)
  route_table_id            = module.vpc_secondary.private_route_table_ids[count.index]
  destination_cidr_block    = module.vpc_primary.vpc_cidr_block
  vpc_peering_connection_id = aws_vpc_peering_connection.primary_to_secondary.id
}

