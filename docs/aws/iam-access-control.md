# AWS IAM Identity Center and Access Control

## 1. Overview

The Recipe Suggestion App uses **AWS IAM Identity Center** to centrally manage team member access to AWS resources.

The system follows Role-Based Access Control (RBAC) and the principle of least privilege. Team members receive permissions based on their development responsibilities.

This configuration supports secure cloud development and deployment for the Cloud Computing project.

## 2. IAM vs. IAM Identity Center

**AWS IAM** manages policies, roles, and permissions within AWS accounts. It also provides roles used by AWS services such as EC2, CloudFormation, and CodeBuild.

**AWS IAM Identity Center** manages human access to AWS accounts through centralized authentication and permission sets.

When a permission set is assigned to a group for an AWS account, Identity Center provisions a corresponding IAM role in that account.

Team members use temporary credentials through Identity Center instead of permanent IAM access keys.

Application users are separate from AWS developers. The Recipe Suggestion App plans to use Amazon Cognito for customer authentication.

## 3. Current Configuration

| Component | Configuration |
|---|---|
| AWS Region | `us-east-1` |
| Identity management | AWS IAM Identity Center |
| Administrator group | `admin` |
| Backend group | `RecipeApp-Backend` |
| Frontend group | `RecipeApp-Frontend` |
| Administrator permission set | `AdministratorAccess` |
| Backend permission set | `RecipeApp-BackendDev` |
| Frontend permission set | `RecipeApp-FrontendDev` |
| AWS CLI profile | `recipe-app` |

The groups have been assigned to the project AWS account.

The corresponding IAM Identity Center roles have been observed in AWS IAM.

## 4. Team Roles and Permissions

### Administrator

**Group:** `admin`

**Permission set:** `AdministratorAccess`

Administrators manage AWS infrastructure, Identity Center assignments, CloudFormation templates, deployment pipelines, and other project resources.

Administrative access must be restricted to authorized infrastructure maintainers.

### Backend Developer

**Group:** `RecipeApp-Backend`

**Permission set:** `RecipeApp-BackendDev`

Configured AWS managed policies:

- `AmazonEC2ReadOnlyAccess`
- `CloudWatchLogsReadOnlyAccess`

These allow developers to inspect EC2 resources and CloudWatch Logs without granting general infrastructure modification permissions.

These managed policies may provide read access to resources outside this project. Resource-scoped policies should be considered as the infrastructure matures.

### Frontend Developer

**Group:** `RecipeApp-Frontend`

**Permission set:** `RecipeApp-FrontendDev`

Configured AWS managed policies:

- `AmazonS3ReadOnlyAccess`
- `CloudFrontReadOnlyAccess`

These support inspection of frontend hosting resources.

The policies may allow broader account-wide read access than required. They should be refined when the frontend resources are deployed.

## 5. Team Member Onboarding

1. Open AWS IAM Identity Center.
2. Navigate to **Users → Add user**.
3. Create an individual account using the teammate's email address.
4. Assign the user to `RecipeApp-Backend` or `RecipeApp-Frontend`.
5. Ensure the group has an AWS account assignment with the correct permission set.
6. Have the teammate activate their account and configure MFA.
7. Verify the teammate can access the project AWS account through the AWS access portal.

A team member may belong to multiple groups if their responsibilities require it.

No separate IAM user is required for developers.

## 6. AWS CLI Configuration

Developers should install AWS CLI v2 and authenticate using IAM Identity Center.

Verify installation:

```bash
aws --version
```

Start configuration:

```bash
aws configure sso
```

Use the following values:

| Setting | Value |
|---|---|
| SSO session name | `recipe-app-session` |
| SSO start URL | Project AWS access portal URL |
| SSO Region | Identity Center's configured Region |
| Default client Region | `us-east-1` |
| Output format | `json` |
| CLI profile name | `recipe-app` |

The AWS access portal URL should be obtained from IAM Identity Center.

Each developer selects the AWS account and permission set available to their identity.

Authenticate:

```bash
aws sso login --profile recipe-app
```

Verify the active identity:

```bash
aws sts get-caller-identity --profile recipe-app
```

Check the configured Region:

```bash
aws configure get region --profile recipe-app
```

If necessary, configure the Region:

```bash
aws configure set region us-east-1 --profile recipe-app
```

For convenient use in a terminal session:

```bash
export AWS_PROFILE=recipe-app
```

The CLI uses temporary credentials obtained through IAM Identity Center.

Do not commit AWS CLI configuration files, cached credentials, or access tokens to the repository.

## 7. Infrastructure and Service Roles

Human access and AWS service access are managed separately.

Planned service roles include:

| AWS service | Purpose |
|---|---|
| EC2 instance role | Allow Django to access approved AWS resources |
| CodeBuild service role | Build and test application code |
| CodePipeline service role | Coordinate deployment |
| CloudFormation execution role | Create and update approved infrastructure |

Service roles should receive only the permissions required for their tasks.

CloudFormation manages infrastructure configuration, while CI/CD automates application builds and deployments.

## 8. Security Principles

The project follows these principles:

- Individual accounts for each team member
- Centralized authentication through IAM Identity Center
- MFA for human access
- Role-based access control
- Least-privilege permissions
- Temporary credentials instead of long-lived access keys
- Separation of human and service identities
- Restricted administrator access
- No credentials committed to GitHub

## 9. Validation Status

| Check | Status |
|---|---|
| Identity Center enabled | Complete |
| Administrator group created | Complete |
| Backend group created | Complete |
| Frontend group created | Complete |
| Permission sets configured | Complete |
| Groups assigned to AWS account | Complete |
| IAM roles provisioned | Complete |
| Administrator AWS CLI SSO authentication | Complete |
| Teammate account activation | Pending verification |
| Teammate console access | Pending verification |
| Developer least-privilege testing | Pending |
| Service roles for deployment | Planned |

A successful AWS account assignment does not by itself prove that the assigned permissions have been tested.

## 10. Future Improvements

Before final deployment:

- Test frontend and backend developer permissions.
- Replace broad managed read-only policies with narrower resource-scoped policies where practical.
- Implement dedicated IAM service roles for AWS deployment services.
- Configure CloudWatch monitoring and logging.
- Review unused IAM users and access keys.
- Document security testing results.

## 11. Midpoint Evaluation

The current IAM implementation demonstrates:

- Centralized identity management
- Role-based access control
- Separation of administrator and developer responsibilities
- AWS account assignments through permission sets
- Automatically provisioned IAM roles
- Secure AWS CLI authentication using temporary credentials

The remaining security validation and service-role configuration will be completed during subsequent infrastructure and deployment work.

## References

- [AWS IAM Identity Center](https://docs.aws.amazon.com/singlesignon/latest/userguide/what-is.html)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [AWS CLI IAM Identity Center Authentication](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html)