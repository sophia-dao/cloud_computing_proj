# AWS Infrastructure

This directory contains the AWS infrastructure configuration for the **Recipe Suggestion App**, managed using AWS CloudFormation.

Infrastructure as Code (IaC) allows the team to create, update, and maintain AWS resources consistently through version-controlled templates.

## 1. Infrastructure Overview

**AWS Region:** `us-east-1`  
**Infrastructure as Code:** AWS CloudFormation  
**Backend hosting:** Amazon EC2 (planned)  
**Frontend hosting:** Amazon S3 and CloudFront (planned)  
**Database:** Amazon RDS (planned)

### Directory Structure

```text
infrastructure/
├── README.md
└── cloudformation/
    └── network.yaml
```

Additional CloudFormation templates will be added as the project progresses.

### Deployment Status

| Component | CloudFormation Stack | Status |
|---|---|---|
| VPC and networking | `recipe-app-network` | Deployed and verified |
| EC2 backend | TBD | Planned |
| Relational database | TBD | Planned |
| CI/CD pipeline | TBD | Planned |

## 2. Prerequisites

Before deploying infrastructure, ensure that:

- AWS CLI v2 is installed.
- AWS IAM Identity Center access is configured.
- The developer has appropriate AWS permissions.
- The AWS CLI profile points to the correct AWS account.
- Commands are executed from the repository root unless otherwise specified.

See [IAM Access Control](../docs/aws/iam-access-control.md) for identity and authentication configuration.

The examples below use the local AWS CLI profile `recipe-app`. Each developer may use their own profile name.

## 3. AWS Authentication

Authenticate using IAM Identity Center:

```bash
aws sso login --profile recipe-app
```

Verify the current AWS identity:

```bash
aws sts get-caller-identity --profile recipe-app
```

Verify the configured Region:

```bash
aws configure get region --profile recipe-app
```

Expected Region:

```text
us-east-1
```

AWS CLI SSO authentication uses temporary credentials rather than permanent IAM access keys.

## 4. Network Infrastructure

**Template:** `cloudformation/network.yaml`  
**Stack:** `recipe-app-network`  
**Deployment date:** October 13, 2026  
**Status:** Deployed and verified

### Network Configuration

| Resource | Configuration |
|---|---|
| VPC | `10.0.0.0/16` |
| Public subnet | `10.0.1.0/24` |
| Internet Gateway | Attached to VPC |
| Public route table | Configured |
| Default route | `0.0.0.0/0` through Internet Gateway |
| Subnet association | Public subnet associated with public route table |

The project uses a dedicated VPC rather than modifying the account's default VPC.

### 4.1 Inspect Existing VPCs

```bash
aws ec2 describe-vpcs \
  --region us-east-1 \
  --profile recipe-app \
  --query 'Vpcs[*].[VpcId,CidrBlock,IsDefault]' \
  --output table
```

This command lists VPC IDs, CIDR blocks, and whether each VPC is the default.

### 4.2 Validate the CloudFormation Template

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

Validation checks whether AWS CloudFormation accepts the template's structure. It does not create resources or guarantee deployment success.

### 4.3 Deploy the Network Stack

```bash
aws cloudformation deploy \
  --template-file infrastructure/cloudformation/network.yaml \
  --stack-name recipe-app-network \
  --region us-east-1 \
  --profile recipe-app
```

Successful deployment output:

```text
Waiting for changeset to be created..
Waiting for stack create/update to complete
Successfully created/updated stack - recipe-app-network
```

The same command can be used to deploy subsequent template updates. Review proposed infrastructure changes before applying updates.

### 4.4 Verify Stack Status

```bash
aws cloudformation describe-stacks \
  --stack-name recipe-app-network \
  --region us-east-1 \
  --profile recipe-app \
  --query 'Stacks[0].[StackName,StackStatus]' \
  --output table
```

Verified result:

```text
recipe-app-network
CREATE_COMPLETE
```

### 4.5 Verify Stack Resources

```bash
aws cloudformation describe-stack-resources \
  --stack-name recipe-app-network \
  --region us-east-1 \
  --profile recipe-app \
  --query 'StackResources[*].[LogicalResourceId,ResourceType,ResourceStatus]' \
  --output table
```

The deployment successfully created all seven CloudFormation resources:

- `RecipeAppVPC`
- `PublicSubnet`
- `InternetGateway`
- `InternetGatewayAttachment`
- `PublicRouteTable`
- `PublicDefaultRoute`
- `PublicSubnetRouteTableAssociation`

All resources were verified with status `CREATE_COMPLETE`.

### 4.6 Inspect Stack Outputs

```bash
aws cloudformation describe-stacks \
  --stack-name recipe-app-network \
  --region us-east-1 \
  --profile recipe-app \
  --query 'Stacks[0].Outputs' \
  --output table
```

Verified deployment outputs:

| Output | Export Name | Value |
|---|---|---|
| VPC ID | `RecipeApp-VpcId` | `vpc-0197766fbe7061905` |
| Public subnet ID | `RecipeApp-PublicSubnetId` | `subnet-0f0f85016b68912bc` |

Other CloudFormation stacks can reference these resources through `Fn::ImportValue`.

These IDs represent the current deployment and may change if resources are recreated.

## 5. Infrastructure Updates

When modifying an existing CloudFormation template:

1. Edit the relevant YAML file.
2. Validate the updated template.
3. Review the proposed changes.
4. Deploy the updated stack.
5. Verify stack status and resource health.
6. Update the documentation if the architecture changes.

For safer updates, use CloudFormation change sets to inspect proposed modifications before execution.

Avoid making manual changes to CloudFormation-managed resources because they can cause configuration drift.

## 6. Infrastructure Cleanup

When the infrastructure is no longer needed, a CloudFormation stack can be deleted.

**Warning:** Deleting stacks can remove infrastructure and associated data. Confirm dependencies and backups before running cleanup commands.

Network stack deletion:

```bash
aws cloudformation delete-stack \
  --stack-name recipe-app-network \
  --region us-east-1 \
  --profile recipe-app
```

Wait for deletion to complete:

```bash
aws cloudformation wait stack-delete-complete \
  --stack-name recipe-app-network \
  --region us-east-1 \
  --profile recipe-app
```

Dependent stacks, such as the future EC2 backend stack, must be removed before deleting the network stack.

Do not run cleanup commands against active project infrastructure without team approval.

## 7. Planned Infrastructure

### Backend Deployment

A future CloudFormation template will provision the Django backend on Amazon EC2.

Planned components include:

- EC2 instance
- Security group
- IAM instance role
- AWS Systems Manager access
- Docker-based Django deployment

### Database

Amazon RDS is planned for persistent relational storage.

SQLite may be used temporarily during the initial cloud demonstration.

### Frontend Hosting

React frontend hosting is planned using Amazon S3 and CloudFront.

### CI/CD

AWS CodePipeline and CodeBuild are being considered for automated application builds and deployment.

### Scalability

Future improvements may include:

- Multiple Availability Zones
- Application Load Balancer
- EC2 Auto Scaling
- Private subnets
- CloudWatch monitoring and alarms

These components are not part of the initial network deployment.

## 8. Architecture Documentation

The AWS architecture will be documented separately, including a VPC network diagram showing:

- VPC CIDR block
- Public and future private subnets
- Internet Gateway
- Routing configuration
- EC2 placement
- Security boundaries
- Future database connectivity

See [AWS Architecture](../docs/aws-architecture.md) for the overall cloud design.

The detailed network diagram will be added after the relevant resources have been deployed and verified.

## 9. Security Notes

- Use IAM Identity Center for developer authentication.
- Avoid permanent IAM access keys.
- Never commit credentials or authentication tokens.
- Grant permissions according to development responsibilities.
- Use dedicated IAM roles for AWS services.
- Restrict network access through security groups.
- Prefer AWS Systems Manager over publicly exposed SSH access.

For additional information, see [IAM Access Control](../docs/aws/iam-access-control.md).