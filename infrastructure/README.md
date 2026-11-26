# Recipe Suggestion App — AWS Infrastructure Deployment

This guide describes how to deploy the Recipe Suggestion App into a **new, authorized AWS account** using the CloudFormation templates and scripts in this repository. It is intended for a course evaluator or developer familiar with AWS CLI basics.

> **Validation status (November 2026):** Templates and scripts have been reviewed and locally syntax-checked during preparation, but the complete procedure has **not yet been verified in a fresh AWS account**. 

## Architecture

```text
Browser --HTTPS--> CloudFront
                     |-- default --> private S3 frontend (OAC)
                     |-- /api/* --> CloudFront VPC origin --> internal ALB
                                                              |
                                                       EC2 Auto Scaling Group
                                                       (private subnets A/B)
                                                              |
                                                       Nginx :80 -> Django :8000
                                                              |
                                             RDS PostgreSQL + private S3 media

Cognito User Pool: sign-in (optional Google federation)
Secrets Manager: Django secret and RDS-managed credentials
SSM Parameter Store: runtime resource names, IDs, and endpoints
VPC endpoints: ECR, S3, SSM, Secrets Manager, CloudWatch Logs
NAT gateway: package installation and external TheMealDB API access
```

The VPC contains public infrastructure for the NAT gateway and private application/database subnets. EC2 instances have no public IPs. The Internet Gateway enables internet access for the public subnet; private instances use the NAT gateway for outbound internet access. The backend is reached publicly **only through CloudFront**, not directly from the internet.

## Prerequisites

- **AWS account and permissions:** A separate, authorized AWS account with sufficient permissions to provision the complete application infrastructure, including CloudFormation, VPC networking, NAT Gateway, VPC endpoints, ALB, EC2/Auto Scaling, IAM roles and policies, ECR, RDS, S3, CloudFront, Cognito, Secrets Manager, and SSM.

- **AWS IAM Identity Center (SSO):** This project's AWS administrative access was configured through IAM Identity Center. For initial deployment and testing, using an account assigned the **AdministratorAccess permission set** is recommended to simplify provisioning of the complete infrastructure. This level of access should be restricted to authorized administrators; a least-privilege permission set is recommended for ongoing operations.

- **AWS CLI and development tools:** AWS CLI v2 configured with an SSO profile for the target account, Docker with Buildx, Python 3, Node.js and npm, and `cfn-lint` for local CloudFormation validation.

- **Project repository:** Access to the repository, including `backend/`, `frontend/`, and `infrastructure/`.

- **AWS Region:** `us-east-1`. The deployment scripts are designed for this region.

- **AWS service quotas and budget:** Sufficient quotas and budget for NAT Gateway, interface VPC endpoints, ALB, EC2, RDS, CloudFront, and associated data transfer. **Charges accrue even while resources are idle.**

- **Google Sign-In (optional):** Google OAuth credentials are required only when enabling Google federation through Amazon Cognito. Native Cognito configuration and Google federation should be checked against the `cognito.yaml` parameters and deployment script before enabling Google.

**Protect credentials:** Do not commit AWS access keys, Google client secrets, production `.env` files, or generated backend environment files. The deployed backend retrieves application secrets from AWS Secrets Manager rather than embedding them in source code.

## Repository layout

```text
infrastructure/
├── README.md
├── cloudformation/
│   ├── network.yaml                 # VPC, subnets, routing, NAT
│   ├── endpoints.yaml               # Private AWS service access
│   ├── alb.yaml                     # Internal load balancer
│   ├── ecr.yaml                     # Backend image repository
│   ├── secrets.yaml                 # Django secret
│   ├── media.yaml                   # Private media bucket
│   ├── backend.yaml                 # Backend IAM and security group
│   ├── rds.yaml                     # PostgreSQL database
│   ├── database-access.yaml         # EC2 permission for RDS secret
│   ├── frontend.yaml                # CloudFront and frontend bucket
│   ├── media-policy.yaml            # Media delivery policy
│   ├── cognito.yaml                 # User Pool and app client
│   ├── config.yaml                  # SSM runtime configuration
│   ├── autoscaling.yaml             # EC2 Launch Template and ASG
│   └── autoscaling-packaged.yaml    # Generated; do not hand-edit
└── scripts/
    ├── deploy.sh
    ├── push-backend.sh
    ├── deploy-autoscaling.sh
    ├── initialize-database.sh
    ├── finalize-autoscaling.sh
    ├── deploy-frontend.sh
    ├── package-autoscaling.py
    ├── bootstrap-backend.sh
    └── start-backend.sh
```

## 1. Configure AWS IAM Identity Center (SSO) and verify the target account

This project uses **AWS IAM Identity Center (SSO)** for AWS administrative access. The deployment workflow was developed using the `AdministratorAccess` permission set, which is recommended for initial infrastructure provisioning and testing.

From the **repository root**, configure an AWS CLI SSO profile:

```bash
aws configure sso
```

Enter the following information when prompted:

```text
SSO session name (Recommended): recipe-app
SSO start URL [None]: <your-aws-access-portal-url>
SSO region [None]: us-east-1
SSO registration scopes [sso:account:access]: [Press Enter]
```

The SSO start URL is provided by your AWS administrator and typically resembles `https://d-xxxxxxxxxx.awsapps.com/start`. The SSO region must match your IAM Identity Center configuration; it is not necessarily the same as the application deployment region.

AWS CLI will attempt to open a browser for authentication. If the browser does not open, follow the displayed URL. Alternatively, use `aws configure sso --use-device-code`.

After successful authentication, select the intended AWS account and permission set when prompted. For this project's initial deployment, select `AdministratorAccess` if available.

Complete the remaining configuration:

```text
Default client Region [None]: us-east-1
CLI default output format (json if not specified) [None]: table
Profile name [AdministratorAccess-<account-id>]: recipe-app
```

If prompted to configure AWS skills or an AWS MCP server for an AI coding agent, this is optional and not required for deployment.

**Note:** The SSO session name and AWS CLI profile name are separate settings. This guide uses `recipe-app` for both to simplify configuration.

### Activate and verify the AWS profile

```bash
export AWS_PROFILE=recipe-app
export AWS_DEFAULT_REGION=us-east-1
```

Verify that the CLI is authenticated:

```bash
aws sts get-caller-identity
```

Confirm that the returned `Account` matches the intended deployment account. **Do not continue if the account ID is incorrect.**

Set the target account ID using the actual value returned:

```bash
export TARGET_ACCOUNT_ID="<your-12-digit-account-id>"
```

The deployment scripts use this account ID as a safety check. They do not create or switch AWS accounts.

### SSO session expiration

AWS SSO sessions may expire during deployment. If authentication fails with a token expiration error, reauthenticate:

```bash
aws sso login --profile recipe-app
```

Then verify access again:

```bash
aws sts get-caller-identity
```

If deployment was interrupted, inspect existing CloudFormation stacks before rerunning any deployment scripts. The scripts are designed to refuse updates to already-existing stacks.

## 2. Validate infrastructure locally

```bash
bash -n infrastructure/scripts/deploy.sh
bash -n infrastructure/scripts/push-backend.sh
bash -n infrastructure/scripts/deploy-autoscaling.sh
bash -n infrastructure/scripts/initialize-database.sh
bash -n infrastructure/scripts/finalize-autoscaling.sh
bash -n infrastructure/scripts/deploy-frontend.sh
bash -n infrastructure/scripts/bootstrap-backend.sh
bash -n infrastructure/scripts/start-backend.sh

python3 infrastructure/scripts/package-autoscaling.py
cfn-lint infrastructure/cloudformation/*.yaml
```

The packaging script embeds the current backend bootstrap/startup scripts into the generated Auto Scaling template. **Run it again after any startup-script change.** Syntax validation cannot confirm runtime permissions, AWS service quotas, or application behavior.

## 3. Deploy foundational AWS infrastructure

```bash
bash infrastructure/scripts/deploy.sh "$TARGET_ACCOUNT_ID"
```

Read the prompts and confirm only after verifying the target account. This script deploys the foundational CloudFormation stacks, including networking, endpoints, ALB, ECR, secrets, media, backend IAM, RDS, frontend/CloudFront, Cognito, and SSM configuration. It **does not** launch the backend Auto Scaling Group.

Wait for the script to finish successfully before proceeding. Inspect failures in CloudFormation **Events**; do not rerun blindly or delete a partially deployed stack without checking dependencies. The script is designed to refuse updates to already-existing stacks.

### Verify Docker and Authenticate with Amazon ECR

Before building and pushing the backend Docker image, ensure Docker is running and authenticate with Amazon ECR:

```bash
# Verify Docker is running
docker info >/dev/null && echo "Docker is running"

# Authenticate Docker with Amazon ECR
aws ecr get-login-password --region us-east-1 \
  | docker login \
      --username AWS \
      --password-stdin \
      "${TARGET_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com"
```

Expected output:

```text
Docker is running
Login Succeeded
```

If an image upload times out, verify your network connection, refresh ECR authentication, and retry the push.


```bash
bash infrastructure/scripts/push-backend.sh "$TARGET_ACCOUNT_ID"
```

This builds the backend for `linux/amd64` and pushes the initial `final-v1` image to the new account's ECR repository. Image tags are immutable: use a **new tag** for subsequent releases and update the corresponding configuration rather than attempting to overwrite `final-v1`.

## 5. Start the initial backend instance

```bash
bash infrastructure/scripts/deploy-autoscaling.sh "$TARGET_ACCOUNT_ID"
```

The initial deployment uses the `InitialDeployment=true` configuration to start **one** instance while database initialization is pending. The script packages the launch template, creates the Auto Scaling stack, and checks Systems Manager connectivity.

At this stage the ALB `/healthz` response is a **Nginx infrastructure check**, not proof that Django can query PostgreSQL. The application may not be fully ready until migrations finish.

## 6. Initialize PostgreSQL and import recipes

```bash
bash infrastructure/scripts/initialize-database.sh "$TARGET_ACCOUNT_ID"
```

After the `INITIALIZE` confirmation, the script uses **AWS Systems Manager Run Command**, not SSH, to execute Django migrations and import up to 100 recipes from TheMealDB. The revised script skips import if the database already contains recipes; if an import partially completed, inspect the data before rerunning. Review the final command status and output for success.

This stage requires outbound access to TheMealDB. External API availability, rate limits, and image downloads can affect the result. Recipe import is **not** a CloudFormation-managed operation.

## 7. Scale to the normal configuration

```bash
bash infrastructure/scripts/finalize-autoscaling.sh "$TARGET_ACCOUNT_ID"
```

After initialization succeeds, this updates the ASG to `InitialDeployment=false` and waits for **two healthy, InService instances** across the private application subnets (normal configuration: minimum 2, desired 2, maximum 3).

## 8. Build and publish the frontend

```bash
bash infrastructure/scripts/deploy-frontend.sh "$TARGET_ACCOUNT_ID"
```

The script obtains CloudFront/Cognito settings from stack outputs, creates a temporary production Vite configuration, builds React, synchronizes `frontend/dist/` to the private S3 frontend bucket, and requests a CloudFront invalidation. It should remove the temporary configuration on exit. Review the script before running if your local frontend `.env` contains old-account values; **never publish those values accidentally**.

CloudFront changes and invalidations may take time to propagate.

## 9. Verify the application

Obtain the frontend URL from CloudFormation outputs (the frontend stack exports `RecipeApp-FrontendURL`). Then check:

- The CloudFront site loads over HTTPS, including a refreshed client-side route.
- The `/api/recipes/` endpoint responds successfully through **CloudFront**, not just locally on EC2.
- Imported recipes and their images display.
- Cognito sign-in, sign-out, and authenticated features work. Test Google Sign-In only if configured.
- The Auto Scaling Group reports two healthy instances and the ALB target group has healthy targets.
- EC2 instances are accessible through Systems Manager without public IP addresses or inbound SSH.
- The database and media bucket are private, and secrets are read from Secrets Manager.

Useful inspection commands:

```bash
aws cloudformation list-stacks --region us-east-1 \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE
aws autoscaling describe-auto-scaling-groups --region us-east-1
aws ssm describe-instance-information --region us-east-1
```

For application-level verification, check the CloudFront `/api/recipes/` response **after** migrations. A `200` from Nginx `/healthz` alone does not prove Django is healthy.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| CloudFormation stack fails | Stack Events, missing cross-stack exports, IAM permissions, quotas, region |
| EC2 not visible in SSM | Instance profile, SSM Agent, endpoint private DNS, endpoint SG port 443, subnet routing |
| Docker image pull fails | ECR image/tag, ECR API and Docker endpoints, S3 gateway route, IAM permissions |
| Backend startup fails | `journalctl -u recipe-app-backend`, `docker logs recipe-app-backend`, SSM parameters and Secrets Manager access |
| ALB healthy but API fails | Nginx `/healthz` only checks infrastructure; inspect Django logs, migrations, database connectivity |
| Recipe import fails | SSM command output, TheMealDB reachability through NAT, database migrations, container state |
| Frontend loads but API fails | CloudFront `/api/*` behavior, VPC origin, ALB target group, Django allowed hosts |
| Cognito callback fails | Exact CloudFront callback/logout URLs, User Pool client, domain, OAuth settings |

On a managed instance, useful diagnostics include `sudo systemctl status recipe-app-backend`, `sudo journalctl -u recipe-app-backend -n 100 --no-pager`, and `sudo docker logs --tail 100 recipe-app-backend`. Do not paste secret values into logs or support tickets.


## Known limitations

- The fresh-account deployment is not yet end-to-end tested.
- The initial Nginx `/healthz` check measures reverse-proxy availability, not database/application readiness.
- TheMealDB is an external dependency during initial data import.
- Google federation requires valid OAuth credentials and matching callback configuration; it is optional for basic deployment.
- This guide documents a manual deployment workflow, not an automated CI/CD pipeline.
- Resources such as NAT gateways, interface endpoints, ALB, and RDS incur charges; remove test environments promptly when no longer needed.
- The initial database pose some limitations in variety of recipes. Therefore, testing the filter function might be difficult if too much filter values are selected
