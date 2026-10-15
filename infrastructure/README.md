# AWS Infrastructure — Recipe Suggestion App

**Last verified:** October 14, 2026 (US Central)  
**Region:** `us-east-1`  
**AWS CLI profile:** `recipe-app`  
**Status:** React frontend deployed through CloudFront; Django API running on EC2 and verified **locally only**. Frontend-to-backend routing is **not yet configured**.

## 1. Architecture

```text
Browser
   |
   | HTTPS
   v
CloudFront distribution (E2YMECNRA0V5YR)
   |
   | Default behavior: static frontend
   v
Private S3 bucket (React/Vite build)

[PLANNED — NOT CONNECTED]
CloudFront /api/* behavior
   |
   | Custom origin via existing Internet Gateway/public subnet
   v
EC2 backend (Docker + Gunicorn + Django)
   |
   v
Temporary SQLite database (host-mounted file)
```

**Important:** The current CloudFront distribution serves the frontend only. There is no public API endpoint, `/api/*` origin behavior, or browser-to-Django connection yet. The planned Internet Gateway design requires additional origin security, stable addressing/DNS, and an appropriate HTTPS/reverse-proxy configuration. CloudFront viewer HTTPS alone does **not** guarantee HTTPS to the EC2 origin.

## 2. Deployment inventory

| Component | CloudFormation stack / resource | Verified state |
| --- | --- | --- |
| VPC, Internet Gateway, route table, two public subnets | `recipe-app-network` | Deployed |
| ECR backend image registry | `recipe-app-ecr` | Deployed; image tagged `midpoint-v1` pushed |
| EC2, IAM role/profile, security group | `recipe-app-backend` | Deployed; instance running |
| Dockerized Django API | Container on EC2 | Running; `/api/ingredients/` returned HTTP 200 from EC2 localhost |
| S3 bucket, CloudFront OAC and distribution | `recipe-app-frontend` | Deployed; CloudFront returned HTTP 200 |
| Systems Manager Session Manager | EC2 IAM role / SSM | Interactive session verified; no inbound SSH rule |
| GitHub OIDC provider | AWS account | Identity provider configured; automated deployments not implemented |
| Public backend API | — | **Not configured** |
| CloudFront API routing | — | **Not configured** |
| Cognito authentication | — | **Not verified/implemented end-to-end** |
| RDS / production database | — | **Not deployed** |
| Automated CI/CD | — | **Not implemented** |
| ALB / Auto Scaling | — | **Not deployed** |

### Infrastructure files

```text
infrastructure/
├── README.md
└── cloudformation/
    ├── network.yaml
    ├── ecr.yaml
    ├── backend.yaml
    └── frontend.yaml
```

## 3. Network

| Resource | Configuration |
| --- | --- |
| VPC | `10.0.0.0/16` (`vpc-0197766fbe7061905`) |
| Original public subnet | `10.0.1.0/24`, currently `us-east-1e` |
| Backend public subnet | `10.0.2.0/24`, `us-east-1a` |
| Internet Gateway | Attached to VPC |
| Public route table | `0.0.0.0/0` routes to Internet Gateway |
| Subnet associations | Both public subnets use public route table |
| Private subnets / NAT Gateway | Not created |

Network exports: `RecipeApp-VpcId`, `RecipeApp-PublicSubnetId`, `RecipeApp-PublicSubnetAId`, and `RecipeApp-PublicRouteTableId`.

**Why two subnets?** The original subnet was in `us-east-1e`; a second subnet was added in `us-east-1a` to launch the chosen EC2 instance type.

## 4. Backend EC2 and security

- **Instance ID:** `i-0f80e33afb9d7dd0a`
- **Type:** `t3.micro`
- **OS:** Amazon Linux 2023 (AMI resolved through the public SSM parameter)
- **Root volume:** 12 GiB encrypted gp3, `DeleteOnTermination: true`
- **Subnet:** public subnet in `us-east-1a`
- **Security group:** `sg-0924c0659e225b906`
- **Instance permissions:** `AmazonSSMManagedInstanceCore`, plus limited ECR image-pull actions
- **IMDS:** IMDSv2 required (`HttpTokens: required`)
- **Administration:** Systems Manager Session Manager; no inbound SSH access configured

### Security group verification

Actual rule query confirmed:

| Direction | Rule |
| --- | --- |
| Inbound | None |
| Outbound | All IPv4 traffic to `0.0.0.0/0` |

CloudFormation drift detection on the backend stack completed with `StackDriftStatus: IN_SYNC` and `DriftedStackResourceCount: 0` on October 14, 2026 (local time; detection timestamp `2026-10-15T00:32:41.916Z`). An earlier summarized security-group query showed empty egress, but a direct `describe-security-group-rules` check confirmed the outbound rule (`sgr-0b193a389807c2e27`). **No security group modifications were made during this investigation.**

### Connect to the instance

```bash
aws sso login --profile recipe-app
aws ssm start-session \
  --target i-0f80e33afb9d7dd0a \
  --region us-east-1 \
  --profile recipe-app
```

## 5. ECR and Django container

**Image:**

```text
362176666546.dkr.ecr.us-east-1.amazonaws.com/recipe-app-backend:midpoint-v1
```

- Built for `linux/amd64` and pushed to ECR.
- Gunicorn serves Django on `0.0.0.0:8000` **inside the container**.
- Docker publishes it only on the EC2 loopback interface: `127.0.0.1:8000:8000`.
- Container name: `recipe-app-backend`.
- Restart policy: `unless-stopped`.
- Temporary SQLite database persists in `/opt/recipe-app/data/db.sqlite3` on the EC2 host and is bind-mounted to `/app/db.sqlite3` inside the container.
- Runtime environment file: `/opt/recipe-app/backend.env`, permissions `600`; contains a Django secret and settings. **Never commit or paste its contents.**
- Django migrations were applied to the mounted SQLite database.

### Current run configuration (for reference)

```bash
sudo docker run -d \
  --name recipe-app-backend \
  --restart unless-stopped \
  --env-file /opt/recipe-app/backend.env \
  -p 127.0.0.1:8000:8000 \
  -v /opt/recipe-app/data/db.sqlite3:/app/db.sqlite3 \
  362176666546.dkr.ecr.us-east-1.amazonaws.com/recipe-app-backend:midpoint-v1
```

> This command documents the existing container setup. Do not run it again while a container with that name already exists. Do not remove the host database file during updates.

### Verified commands on EC2

```bash
sudo docker ps -a
sudo docker inspect recipe-app-backend \
  --format 'Status: {{.State.Status}} Restart: {{.HostConfig.RestartPolicy.Name}} Ports: {{json .HostConfig.PortBindings}}'
curl -i http://127.0.0.1:8000/api/ingredients/
```

Observed: container `running`, restart policy `unless-stopped`, host port bound to `127.0.0.1:8000`, and ingredient API returned **HTTP 200**. This is **not** evidence that the API is reachable from the internet.

## 6. Frontend: S3 + CloudFront

- **Stack:** `recipe-app-frontend`
- **S3 bucket:** `recipe-app-frontend-frontendbucket-yhbrd6afosjk`
- **CloudFront distribution:** `E2YMECNRA0V5YR`
- **URL:** https://d1q0iv2raorz8j.cloudfront.net
- **S3 access:** bucket is private; CloudFront Origin Access Control (OAC) and bucket policy permit delivery through the distribution.
- **SPA behavior:** 403/404 fallback to `index.html`.
- **Viewer protocol:** redirect HTTP to HTTPS.

React/Vite build passed (`npm run build`), and the `frontend/dist/` files were synced to S3. A CloudFront invalidation was created. `curl -I` to the distribution returned **HTTP 200**. Browser-level functionality and API integration were not independently verified.

### Manual frontend release procedure

From the repository root:

```bash
cd frontend
npm ci
npm run build
cd ..
aws s3 sync frontend/dist/ \
  s3://recipe-app-frontend-frontendbucket-yhbrd6afosjk/ \
  --delete --region us-east-1 --profile recipe-app
aws cloudfront create-invalidation \
  --distribution-id E2YMECNRA0V5YR \
  --paths '/*' \
  --profile recipe-app
```

The frontend deployment is currently **manual**. Updating GitHub code or rerunning an unchanged CloudFormation template does **not** automatically build or deploy new application code.

## 7. CloudFormation deployment safety

The stacks are independent deployment units but share exported values:

1. `recipe-app-network` provides VPC/subnet exports.
2. `recipe-app-ecr` provides ECR exports.
3. `recipe-app-backend` imports network and ECR values.
4. `recipe-app-frontend` serves static assets independently.

Validate templates before changes:

```bash
aws cloudformation validate-template \
  --template-body file://infrastructure/cloudformation/backend.yaml \
  --region us-east-1 --profile recipe-app
```

**Before updating a live stack:** create and inspect a CloudFormation change set. Pay special attention to any `Replacement: True` or conditional replacement on `BackendInstance`, VPC, or subnets. The backend AMI parameter resolves to a *latest* Amazon Linux image, so an update could select a different AMI and replace the instance. The host SQLite file resides on a root volume configured for deletion upon instance termination; **back up data before any instance replacement**.

CloudFormation manages infrastructure, **not automatically the currently running Docker container or the React build artifacts**. A failed infrastructure update can affect live resources depending on what was changed and whether rollback succeeds; do not assume all updates are harmless.

## 8. Midpoint deployment decisions and outstanding work

**Decision (October 14):** Use the existing Internet Gateway and public-subnet EC2 for the midpoint API connection, instead of immediately adding private subnets, NAT, ALB, or API Gateway. Route `/api/*` through the existing CloudFront distribution to an EC2 custom origin. This is a **planned implementation**, not a completed deployment.

Before enabling the API route:

1. Establish stable EC2 origin addressing (DNS and/or Elastic IP) and plan certificate handling.
2. Configure an origin-facing reverse proxy/HTTPS listener; do not expose Django development services broadly.
3. Update Docker networking so the reverse proxy can reach Gunicorn while maintaining minimal exposure.
4. Add narrowly scoped inbound security-group rules, preferably restricted to CloudFront origin-facing IP ranges or an appropriate managed prefix list. Validate port and origin reachability.
5. Add a CloudFront custom origin and `/api/*` behavior; forward required methods, headers, query strings, cookies, and authentication data deliberately. Do not cache personalized API responses indiscriminately.
6. Update Django `ALLOWED_HOSTS`, proxy settings, CORS/CSRF settings where applicable, and React API base URL.
7. Test requests end-to-end from a browser, not only with localhost `curl`.

**Remaining after midpoint:** verify Cognito integration; add RDS or another appropriate production database; implement GitHub OIDC-backed CI/CD; evaluate ALB/Auto Scaling and quantify scalability using tests and metrics. Current single-instance deployment is not horizontally scalable and has a single point of failure.

## 9. Security and operational notes

- Do not commit `/opt/recipe-app/backend.env`, Django secrets, AWS credentials, or SQLite data.
- Use SSM instead of opening port 22.
- Preserve the private S3 bucket and CloudFront OAC.
- Keep origin security restrictive; CloudFront HTTPS for viewers does not imply encryption on the CloudFront-to-EC2 hop.
- ECR `midpoint-v1` is immutable; publish a **new tag** for a changed image rather than overwriting it.
- Maintain backups before CloudFormation operations that might replace EC2 or delete EBS storage.
- AWS resources may incur ongoing charges even when lightly used. Review EC2, CloudFront, EBS, and any newly introduced resources.

## 10. Quick verification commands

```bash
# Stack states
aws cloudformation describe-stacks \
  --stack-name recipe-app-backend \
  --region us-east-1 --profile recipe-app \
  --query 'Stacks[0].StackStatus' --output text

# Security group rules
aws ec2 describe-security-group-rules \
  --filters Name=group-id,Values=sg-0924c0659e225b906 \
  --region us-east-1 --profile recipe-app

# Frontend HTTP headers
curl -I https://d1q0iv2raorz8j.cloudfront.net

# Backend API (run INSIDE the EC2 SSM session)
curl -i http://127.0.0.1:8000/api/ingredients/
```

**Next infrastructure task:** connect CloudFront `/api/*` to a secured EC2 origin using the existing Internet Gateway, then verify the full frontend-to-backend request path.
