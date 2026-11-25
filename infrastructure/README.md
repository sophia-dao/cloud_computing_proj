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

- A separate AWS account with permission to create CloudFormation, VPC networking, NAT gateway, endpoints, ALB, EC2/Auto Scaling, IAM roles and policies, ECR, RDS, S3, CloudFront, Cognito, Secrets Manager, and SSM resources. An administrator may need to approve IAM capabilities and service quotas.
- AWS CLI v2 configured with credentials for the **target** account; Docker with Buildx; Python 3; Node.js and npm; `cfn-lint` for local validation.
- Access to the project repository, including `backend/`, `frontend/`, and `infrastructure/`.
- Region **`us-east-1`**. The deployment scripts are designed for this region.
- Enough service quotas and budget for a NAT gateway, multiple interface VPC endpoints, ALB, EC2, RDS, CloudFront, and associated data transfer. **Charges accrue even while idle.**
- Optional: Google OAuth credentials if testing Google Sign-In. Native Cognito configuration and Google federation must be checked against the `cognito.yaml` parameters and deployment script before enabling Google.

**Protect credentials:** Do not commit AWS keys, Google client secrets, production `.env` files, or generated backend environment files. The deployed backend reads secrets from AWS Secrets Manager rather than embedding them in source code.

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

## 1. Select and verify the target AWS account

From the **repository root**, configure a dedicated AWS CLI profile for the new account.

- **AWS CLI v2 with AWS IAM Identity Center (SSO):** This project's deployment workflow was developed and tested using AWS SSO authentication rather than long-lived IAM access keys. Users should configure an AWS CLI SSO profile and authenticate before running the deployment scripts.

  ```bash
  aws configure sso
  aws sso login --profile <your-profile-name>
  aws sts get-caller-identity --profile <your-profile-name>
  ```

  Verify that the returned AWS account ID matches the intended deployment account. Set `AWS_PROFILE` to the configured profile before running the scripts.

  **Note:** AWS SSO sessions may expire during deployment. If authentication fails with a token expiration error, run `aws sso login --profile <your-profile-name>` again. If a deployment was interrupted, inspect existing CloudFormation stacks before retrying.


Confirm that the returned `Account` is the intended account. **Do not continue if it is the existing project account.** Save the 12-digit account ID:

```bash
export TARGET_ACCOUNT_ID="123456789012"  # REPLACE with the actual new account ID
```

The scripts that accept an account ID use it as a safety check; they do not create or switch AWS accounts. Recheck the CLI identity before each major deployment or cleanup operation. If using AWS SSO, sign in to the chosen profile first.

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

## 4. Build and push the backend image

Make sure Docker is running, then execute:

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
