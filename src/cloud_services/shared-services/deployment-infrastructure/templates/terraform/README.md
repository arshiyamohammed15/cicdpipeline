# Terraform Infrastructure Templates

This directory contains Terraform infrastructure-as-code templates for ZeroUI Deployment & Infrastructure Module (EPC-8).

## Usage

### Prerequisites

- Terraform >= 1.0.0
- AWS CLI configured with appropriate credentials
- Backend configuration (S3 bucket for state storage)

### Initialize Terraform

```bash
cd templates/terraform
terraform init
```

### Configure Variables

Create a `terraform.tfvars` file:

```hcl
project_name = "zeroui"
environment  = "development"
region       = "us-east-1"
```

### Plan Infrastructure

```bash
terraform plan
```

### Apply Infrastructure

```bash
terraform apply
```

### Destroy Infrastructure

```bash
terraform destroy
```

## Resource Naming Convention

Resources follow the naming convention: `{project}-{environment}-{resource-type}-{identifier}`

Example: `zeroui-prod-db-primary`

## Backend Configuration

Configure Terraform backend via environment variables or `-backend-config`:

```bash
terraform init \
  -backend-config="bucket=zeroui-terraform-state" \
  -backend-config="key=deployment-infrastructure/terraform.tfstate" \
  -backend-config="region=us-east-1"
```

## Notes

- This is a template - customize for your specific infrastructure needs
- Review and adjust security group rules for your use case
- Configure backend state storage appropriately for your environment
