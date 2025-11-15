# Terraform infrastructure template for ZeroUI Deployment & Infrastructure Module (EPC-8)
#
# What: Vendor-neutral infrastructure-as-code template for ZeroUI ecosystem
# Why: Provides standardized infrastructure provisioning across environments
# Reads/Writes: Reads variables, writes infrastructure state
# Contracts: Infrastructure configuration schema
# Risks: Infrastructure misconfiguration, resource naming conflicts

terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    # Configure backend via environment variables or terraform init -backend-config
    # bucket = "zeroui-terraform-state"
    # key    = "deployment-infrastructure/terraform.tfstate"
    # region = "us-east-1"
  }
}

# Variables
variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "zeroui"
}

variable "environment" {
  description = "Environment (development, staging, production)"
  type        = string
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production"
  }
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Local values for resource naming
locals {
  resource_prefix = "${var.project_name}-${var.environment}"

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Module      = "EPC-8"
  }
}

# Provider configuration
provider "aws" {
  region = var.region

  default_tags {
    tags = local.common_tags
  }
}

# Example: VPC (Virtual Private Cloud)
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${local.resource_prefix}-vpc"
  }
}

# Example: Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${local.resource_prefix}-igw"
  }
}

# Example: Subnet
resource "aws_subnet" "main" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.region}a"
  map_public_ip_on_launch = true

  tags = {
    Name = "${local.resource_prefix}-subnet-main"
  }
}

# Example: Security Group
resource "aws_security_group" "main" {
  name        = "${local.resource_prefix}-sg-main"
  description = "Security group for ZeroUI deployment infrastructure"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.resource_prefix}-sg-main"
  }
}

# Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "subnet_id" {
  description = "Subnet ID"
  value       = aws_subnet.main.id
}

output "security_group_id" {
  description = "Security Group ID"
  value       = aws_security_group.main.id
}
