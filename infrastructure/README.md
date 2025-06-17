# NexaFi Infrastructure as Code (IaC)

## Overview
This directory contains the Infrastructure as Code (IaC) for the NexaFi project. The goal is to define and manage the entire infrastructure required for deploying and operating the NexaFi backend and frontend services using Kubernetes on AWS. The design prioritizes high availability, disaster recovery, and adherence to financial industry compliance standards.

## Architecture
The infrastructure is designed for robust resilience and disaster recovery, leveraging a multi-region AWS setup with Amazon Elastic Kubernetes Service (EKS) for container orchestration. Key architectural components and their alignment with financial industry standards include:

- **Multi-Region AWS Deployment**: Configured across primary and secondary AWS regions to ensure business continuity and disaster recovery capabilities, critical for financial services.

- **Virtual Private Clouds (VPCs)**: Dedicated VPCs are established in both primary and secondary regions, segmented into public, private, and database subnets. **VPC Flow Logs are enabled and configured for comprehensive network traffic monitoring and auditing**, providing essential data for security and compliance requirements.

- **VPC Peering**: A secure peering connection is established between the primary and secondary VPCs, facilitating compliant and efficient cross-region communication for data replication and failover scenarios.

- **Amazon EKS Clusters**: Kubernetes clusters are deployed in both primary and secondary regions, designed for workload isolation and regulatory compliance.
  - **Primary EKS Cluster**: Includes dedicated managed node groups for `financial_services` workloads, with specific taints to ensure sensitive financial applications run on isolated and appropriately configured nodes. A separate `compliance_monitoring` node group is also provisioned for audit and monitoring tools, further enhancing regulatory adherence.
  - **Secondary EKS Cluster**: Features a minimal `dr_standby` node group, strategically designed for rapid scaling during disaster recovery events, ensuring minimal downtime and data loss.

- **AWS Fargate Profiles**: Utilized for running serverless workloads, such as **audit logs**, within the EKS clusters. This provides an immutable and scalable environment for critical compliance-related data.

- **Encryption**: **AWS Key Management Service (KMS) is extensively used for encrypting EKS clusters and Elastic Block Store (EBS) volumes**, ensuring all data at rest is protected in accordance with stringent financial data security regulations.

- **Security Groups**: Custom security groups are meticulously configured for EKS nodes, implementing **strict ingress and egress rules based on the principle of least privilege** to control network traffic and prevent unauthorized access, a cornerstone of financial security.

## Directory Structure
```
infra/
├── kubernetes/
│   ├── core-services/        # Kubernetes manifests for backend microservices
│   │   ├── api-gateway.yaml
│   │   ├── user-service.yaml
│   │   ├── ledger-service.yaml
│   │   ├── payment-service.yaml
│   │   ├── ai-service.yaml
│   │   ├── analytics-service.yaml
│   │   ├── credit-service.yaml
│   │   └── document-service.yaml
│   ├── infrastructure-components/ # Kubernetes manifests for supporting infrastructure
│   │   ├── redis.yaml
│   │   ├── rabbitmq.yaml
│   │   ├── elasticsearch.yaml
│   │   └── kibana.yaml
│   ├── ingress/              # Ingress controller and rules
│   │   └── nginx-ingress.yaml
│   ├── storage/              # Persistent volume claims
│   │   └── pv-pvc.yaml
│   └── namespaces.yaml       # Kubernetes namespaces
├── terraform/                # Terraform configurations for AWS infrastructure
│   ├── main.tf               # Main Terraform configuration, defines providers, variables, and S3 backend
│   ├── vpc.tf                # VPC and networking configurations for primary and secondary regions, including VPC peering
│   ├── eks.tf                # EKS cluster configurations for primary and secondary regions, including node groups and Fargate profiles
│   └── security.tf           # Security related configurations (e.g., KMS keys, IAM roles)
├── helm-charts/              # Helm charts for application deployment (future)
├── scripts/                  # Deployment and management scripts
│   ├── deploy-all.sh
│   ├── delete-all.sh
│   ├── setup-kube.sh
│   └── update-kubeconfig.sh
└── README.md                 # This file
```

## Technologies Used
- **Terraform**: Infrastructure as Code for provisioning and managing AWS resources, ensuring version-controlled and auditable infrastructure deployments.
- **AWS EKS**: Managed Kubernetes service for container orchestration, providing a secure and scalable platform for financial applications.
- **AWS VPC**: Networking for isolated and secure cloud resources, with granular control over network access.
- **AWS KMS**: Key Management Service for cryptographic operations, crucial for data encryption and regulatory compliance.
- **Kubernetes**: Container orchestration, enabling efficient deployment and management of microservices.
- **Docker**: Containerization, ensuring consistent application environments.
- **Helm (future)**: Package management for Kubernetes applications, for streamlined deployments.
- **kubectl**: Kubernetes command-line tool for cluster interaction.

## Deployment Workflow
1. **Setup AWS Credentials**: Ensure your AWS CLI is configured with appropriate credentials and permissions, adhering to least privilege principles.
2. **Initialize Terraform**: Navigate to the `terraform/` directory and run `terraform init` to set up the S3 backend (for state management and collaboration) and download necessary providers.
3. **Plan Terraform Deployment**: Run `terraform plan` to review the infrastructure changes. This step is critical for auditing and ensuring proposed changes align with compliance requirements.
4. **Apply Terraform Deployment**: Execute `terraform apply` to provision the AWS infrastructure (VPCs, EKS clusters, etc.). This process is automated and auditable.
5. **Configure kubectl**: Update your `kubeconfig` to connect to the newly created EKS clusters (refer to `scripts/update-kubeconfig.sh`). Access controls are managed via IAM roles integrated with EKS.
6. **Deploy Infrastructure Components**: Apply Kubernetes manifests for supporting services like Redis, RabbitMQ, Elasticsearch, and Kibana (refer to `kubernetes/infrastructure-components/`). These components are configured with security best practices in mind.
7. **Deploy Core Services**: Apply Kubernetes manifests for all NexaFi microservices (refer to `kubernetes/core-services/`). Application deployments follow secure coding and deployment guidelines.
8. **Configure Ingress**: Set up ingress rules for external access to services (refer to `kubernetes/ingress/`). Ingress configurations are designed to enforce secure communication (e.g., HTTPS).

## Getting Started
Refer to the `scripts/` directory for automated deployment and management scripts. These scripts are designed to facilitate consistent and repeatable deployments.

## Future Enhancements
- **Helm Charts**: For easier deployment and management of complex applications, enabling standardized and versioned application releases.
- **Service Mesh**: Implement Istio or Linkerd for advanced traffic management, security, and observability, crucial for microservices architectures in financial environments.
- **Automated Scaling**: Horizontal Pod Autoscalers (HPA) and Cluster Autoscaler for dynamic resource allocation, ensuring performance and cost efficiency while maintaining stability.
- **Monitoring & Alerting**: Prometheus and Grafana integration for comprehensive infrastructure and application monitoring, with real-time alerts for critical events to ensure operational resilience and compliance.
- **Secret Management**: Integration with dedicated secret management solutions like AWS Secrets Manager or HashiCorp Vault for sensitive data, enhancing security beyond Kubernetes native secrets.
- **CI/CD Pipelines**: Integrate with Jenkins, GitLab CI, or GitHub Actions for automated, secure, and auditable deployments, enforcing a robust change management process.


