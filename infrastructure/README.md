# AWS Infrastructure Deployment Guide

## Overview

This directory contains the Infrastructure as Code (IaC) configuration for the Recipe Suggestion App.

We use AWS CloudFormation to provision and manage AWS resources consistently and reproducibly.

**AWS Region:** `us-east-1`  
**AWS CLI Profile:** `recipe-app`  
**Infrastructure Tool:** AWS CloudFormation

## Prerequisites

- AWS CLI v2 installed
- AWS IAM Identity Center account configured
- AWS CLI SSO profile created
- Appropriate AWS permissions for CloudFormation and EC2

For authentication configuration, see [IAM Access Control](../docs/aws/iam-access-control.md).

## 1. Verify AWS Authentication

Authenticate if necessary:

```bash
aws sso login --profile recipe-app
```

Verify the current AWS identity:

```bash
aws sts get-caller-identity --profile recipe-app
```

Confirm that the returned account is the intended project AWS account.

## 2. Inspect Existing VPCs

Before provisioning network resources:

```bash
aws ec2 describe-vpcs \
  --region us-east-1 \
  --profile recipe-app \
  --query 'Vpcs[*].[VpcId,CidrBlock,IsDefault]' \
  --output table
```

Initial inspection found only the AWS default VPC:

- VPC CIDR: `172.31.0.0/16`
- Default VPC: `true`

The project will use a separate CloudFormation-managed VPC.

## 3. Network Infrastructure

**Template:** `cloudformation/network.yaml`

The initial network stack defines:

- VPC: `10.0.0.0/16`
- Public subnet: `10.0.1.0/24`
- Internet Gateway
- Public route table
- Default internet route
- Route table association

### Validate the CloudFormation Template

Run from the repository root:

```bash
aws cloudformation validate-template \
  --template-body file://infrastructure/cloudformation/network.yaml \
  --region us-east-1 \
  --profile recipe-app
```

Expected output:

```json
{
  "Parameters": [],
  "Description": "Recipe Suggestion App - Initial VPC infrastructure"
}
```

**Validation status:** Passed on October 13, 2026.

Validation confirms that CloudFormation accepts the template's structure. It does not guarantee that resource creation will succeed.

### Deploy the Network Stack

### Deployment Status

**Status:** Deployed successfully on October 13, 2026.

**CloudFormation stack:** `recipe-app-network`

**Region:** `us-east-1`

**Deployment command:**

```bash
aws cloudformation deploy \
  --template-file infrastructure/cloudformation/network.yaml \
  --stack-name recipe-app-network \
  --region us-east-1 \
  --profile recipe-app
```

CloudFormation successfully created or updated the network stack. Resource-level verification is performed using the commands documented above.

### Verify Stack Status

```bash
aws cloudformation describe-stacks \
  --stack-name recipe-app-network \
  --region us-east-1 \
  --profile recipe-app \
  --query 'Stacks[0].[StackName,StackStatus]' \
  --output table
```

Expected successful status:

`CREATE_COMPLETE`

### Inspect Stack Resources

```bash
aws cloudformation describe-stack-resources \
  --stack-name recipe-app-network \
  --region us-east-1 \
  --profile recipe-app
```

### Inspect Stack Outputs

```bash
aws cloudformation describe-stacks \
  --stack-name recipe-app-network \
  --region us-east-1 \
  --profile recipe-app \
  --query 'Stacks[0].Outputs' \
  --output table
```

The stack exports the VPC ID and public subnet ID for use by other CloudFormation templates.

## 4. Infrastructure Updates

After changing the template, validate it again and run the same `aws cloudformation deploy` command.

CloudFormation will create or update resources based on the template changes.

Review changes carefully before applying them, especially if they could replace or delete existing resources.

## 5. Infrastructure Cleanup

To delete the network stack when it is no longer needed:

```bash
aws cloudformation delete-stack \
  --stack-name recipe-app-network \
  --region us-east-1 \
  --profile recipe-app
```

Only delete the network stack after dependent resources and stacks have been removed.

**Warning:** Deleting infrastructure can permanently remove resources and associated data. Do not run cleanup commands during active development without confirming dependencies.

## 6. Planned Infrastructure

| Component | Planned Template | Status |
|---|---|---|
| VPC and networking | `network.yaml` | Deployed - verification pending |
| EC2 backend | `backend.yaml` | Planned |
| Relational database | `database.yaml` | Planned |
| CI/CD pipeline | To be determined | Planned |

## 7. Architecture Documentation

A detailed network diagram will be added after the VPC is deployed and its resources are verified.

The diagram will document the VPC CIDR, subnet boundaries, internet routing, EC2 placement, and relevant security controls.