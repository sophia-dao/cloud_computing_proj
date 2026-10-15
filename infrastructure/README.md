# AWS Infrastructure

Infrastructure as Code (IaC) for the **Recipe Suggestion App**, managed with AWS CloudFormation. Templates are version-controlled and deployed to **`us-east-1`**.

> **Current state (October 14, 2026):** Networking, the ECR repository, and EC2 infrastructure have been deployed. The backend Docker image has been pushed to ECR. Running Django on EC2, public API access, and production database storage are **not yet complete**.

## 1. Architecture and deployment status

| Component | Stack | Status |
| --- | --- | --- |
| Dedicated VPC, Internet Gateway, routing, two public subnets | `recipe-app-network` | Deployed |
| Backend container registry | `recipe-app-ecr` | Deployed; `midpoint-v1` image pushed |
| EC2, security group, IAM instance role | `recipe-app-backend` | Deployed (`CREATE_COMPLETE`) |
| Django container on EC2 | — | Pending |
| Persistent production database (Amazon RDS) | — | Planned |
| React frontend (S3 + CloudFront) | — | Planned |
| CI/CD | — | Planned |

### Directory structure

```text
infrastructure/
├── README.md
├── cloudformation/
│   ├── network.yaml
│   ├── ecr.yaml
│   ├── backend.yaml
│   └── api-access.yaml     # optional: opens the API port to one CIDR
└── scripts/
    └── deploy-backend.sh   # runs the ECR image on EC2 via SSM Run Command
```

> **Running Django on EC2:** see the step-by-step runbook in [docs/midpoint/README.md §3](../docs/midpoint/README.md#3-deployment-runbook-reproducible). `api-access.yaml` is a separate stack so the API port can be opened and closed without updating `backend.yaml`. Updating that stack could replace the instance if the latest-AMI parameter has changed.

### Network configuration

| Resource | Configuration |
| --- | --- |
| VPC | `10.0.0.0/16` |
| Original public subnet | `10.0.1.0/24` (currently `us-east-1e`) |
| Backend public subnet | `10.0.2.0/24` (`us-east-1a`) |
| Internet Gateway | Attached to the dedicated VPC |
| Public route table | Default route `0.0.0.0/0` to Internet Gateway |
| Route table associations | Both public subnets |
| Backend instance | Single EC2 instance in `us-east-1a` |

The second subnet was added because `t3.micro` was unavailable in `us-east-1e` for this account. **Two subnets do not make the application highly available:** only one EC2 instance is deployed.

The backend security group currently has **no inbound rules**. SSH (port 22) is not exposed; EC2 administration uses AWS Systems Manager Session Manager. The API is not publicly reachable yet.

## 2. Prerequisites and authentication

- AWS CLI v2 installed and configured for IAM Identity Center (SSO).
- AWS account permissions for CloudFormation, VPC, ECR, EC2, and IAM.
- Docker installed locally to build and push images.
- Session Manager plugin installed locally to open interactive EC2 sessions.
- Run repository-relative commands from the **repository root**.

The commands below use the local profile `recipe-app`; other developers should substitute their own profile name.

```bash
aws sso login --profile recipe-app
aws sts get-caller-identity --profile recipe-app
aws configure get region --profile recipe-app
```

Expected region: `us-east-1`. SSO uses temporary credentials rather than permanent IAM user access keys.

See [IAM Access Control](../docs/aws/iam-access-control.md) for project access-control documentation.

## 3. VPC and networking

**Template:** `infrastructure/cloudformation/network.yaml`  
**Stack:** `recipe-app-network`

### Inspect existing VPCs

```bash
aws ec2 describe-vpcs \
  --region us-east-1 \
  --profile recipe-app \
  --query 'Vpcs[*].[VpcId,CidrBlock,IsDefault]' \
  --output table
```

### Validate and deploy

```bash
aws cloudformation validate-template \
  --template-body file://infrastructure/cloudformation/network.yaml \
  --region us-east-1 \
  --profile recipe-app

aws cloudformation deploy \
  --template-file infrastructure/cloudformation/network.yaml \
  --stack-name recipe-app-network \
  --region us-east-1 \
  --profile recipe-app
```

Validation checks the template format and references that CloudFormation can validate; it does **not** guarantee a successful deployment.

### Verify the network

```bash
aws cloudformation describe-stacks \
  --stack-name recipe-app-network \
  --region us-east-1 \
  --profile recipe-app \
  --query 'Stacks[0].[StackName,StackStatus]' \
  --output table

aws cloudformation describe-stack-resources \
  --stack-name recipe-app-network \
  --region us-east-1 \
  --profile recipe-app \
  --query 'StackResources[*].[LogicalResourceId,ResourceType,ResourceStatus]' \
  --output table

aws cloudformation describe-stacks \
  --stack-name recipe-app-network \
  --region us-east-1 \
  --profile recipe-app \
  --query 'Stacks[0].Outputs' \
  --output table
```

Known outputs:

| Export | Purpose |
| --- | --- |
| `RecipeApp-VpcId` | Shared VPC reference |
| `RecipeApp-PublicSubnetId` | Original public subnet |
| `RecipeApp-PublicSubnetAId` | Backend public subnet (`us-east-1a`) |
| `RecipeApp-PublicRouteTableId` | Public route table |

The deployed VPC ID is `vpc-0197766fbe7061905`. Resource IDs may change if stacks are recreated; prefer CloudFormation exports over hardcoding IDs in templates.

## 4. Amazon ECR

**Template:** `infrastructure/cloudformation/ecr.yaml`  
**Stack:** `recipe-app-ecr`  
**Repository:** `recipe-app-backend`

The repository stores versioned backend Docker images, uses immutable tags, enables scanning on push, and encrypts images at rest.

### Validate and deploy

```bash
aws cloudformation validate-template \
  --template-body file://infrastructure/cloudformation/ecr.yaml \
  --region us-east-1 \
  --profile recipe-app

aws cloudformation deploy \
  --template-file infrastructure/cloudformation/ecr.yaml \
  --stack-name recipe-app-ecr \
  --region us-east-1 \
  --profile recipe-app
```

### Verify repository and image

```bash
aws ecr describe-repositories \
  --repository-names recipe-app-backend \
  --region us-east-1 \
  --profile recipe-app

aws ecr describe-images \
  --repository-name recipe-app-backend \
  --image-ids imageTag=midpoint-v1 \
  --region us-east-1 \
  --profile recipe-app
```

### Build and push from a development machine

The EC2 template uses an x86_64 Amazon Linux 2023 AMI, so the image must support `linux/amd64`.

```bash
aws ecr get-login-password \
  --region us-east-1 \
  --profile recipe-app \
  | docker login \
      --username AWS \
      --password-stdin \
      362176666546.dkr.ecr.us-east-1.amazonaws.com

docker build --platform linux/amd64 \
  -t recipe-app-backend:midpoint-v1 \
  ./backend

docker tag recipe-app-backend:midpoint-v1 \
  362176666546.dkr.ecr.us-east-1.amazonaws.com/recipe-app-backend:midpoint-v1

docker push \
  362176666546.dkr.ecr.us-east-1.amazonaws.com/recipe-app-backend:midpoint-v1
```

Use a **new image tag** for future releases because the ECR repository uses immutable tags.

CloudFormation exports the repository URI and ARN for use by other stacks. The EC2 instance role has ECR pull permissions, not push permissions.

## 5. EC2 backend infrastructure

**Template:** `infrastructure/cloudformation/backend.yaml`  
**Stack:** `recipe-app-backend`  
**Instance type:** `t3.micro`  
**Operating system:** Amazon Linux 2023

The template provisions:

- An EC2 instance in `RecipeApp-PublicSubnetAId` (`us-east-1a`).
- An encrypted 12 GiB gp3 root EBS volume.
- A security group with no inbound rules initially.
- An IAM instance profile for Systems Manager and read-only ECR image retrieval.
- IMDSv2-required instance metadata.
- User data that installs and starts Docker and creates `/opt/recipe-app/data`.

### Validate and deploy

```bash
aws cloudformation validate-template \
  --template-body file://infrastructure/cloudformation/backend.yaml \
  --region us-east-1 \
  --profile recipe-app

aws cloudformation deploy \
  --template-file infrastructure/cloudformation/backend.yaml \
  --stack-name recipe-app-backend \
  --capabilities CAPABILITY_IAM \
  --region us-east-1 \
  --profile recipe-app
```

### Verify EC2

```bash
aws cloudformation describe-stacks \
  --stack-name recipe-app-backend \
  --region us-east-1 \
  --profile recipe-app \
  --query 'Stacks[0].[StackStatus,Outputs]' \
  --output json

aws ec2 describe-instances \
  --instance-ids i-0f80e33afb9d7dd0a \
  --region us-east-1 \
  --profile recipe-app \
  --query 'Reservations[].Instances[].[InstanceId,State.Name,Placement.AvailabilityZone,PublicIpAddress]' \
  --output table
```

**Verified stack status:** `CREATE_COMPLETE`  
**Deployed instance ID:** `i-0f80e33afb9d7dd0a`  
**Reported public IPv4:** `184.192.191.75` (may change after instance stop/start)

The instance's public IP does **not** mean the API is publicly accessible: the security group currently denies inbound connections.

### Verify Systems Manager registration

```bash
aws ssm describe-instance-information \
  --filters Key=InstanceIds,Values=i-0f80e33afb9d7dd0a \
  --region us-east-1 \
  --profile recipe-app \
  --query 'InstanceInformationList[].[InstanceId,PingStatus,PlatformName]' \
  --output table
```

**Verified result:** `Online` / `Amazon Linux`.

## 6. Connect to EC2 with Session Manager

Session Manager avoids opening SSH port 22 and does not require an EC2 SSH key pair. The local Session Manager plugin is required for AWS CLI interactive sessions.

### Install and verify the plugin (macOS)

```bash
brew install --cask session-manager-plugin
session-manager-plugin
```

If the Homebrew cask is unavailable, follow the [AWS macOS installation guide](https://docs.aws.amazon.com/systems-manager/latest/userguide/install-plugin-macos-overview.html).

### Open a session

```bash
aws ssm start-session \
  --target i-0f80e33afb9d7dd0a \
  --region us-east-1 \
  --profile recipe-app
```

Inside the instance, check the Docker installation and bootstrap status:

```bash
docker --version
sudo systemctl is-active docker
cat /opt/recipe-app/setup-status.txt
```

Expected bootstrap message: `EC2 Docker setup completed`. **These checks are pending confirmation.**

### Pull the backend image on EC2 (next step)

The following commands run **inside EC2**, where the instance role provides ECR permissions. Do not use the local SSO profile on EC2.

```bash
aws ecr get-login-password --region us-east-1 \
  | sudo docker login \
      --username AWS \
      --password-stdin \
      362176666546.dkr.ecr.us-east-1.amazonaws.com

sudo docker pull \
  362176666546.dkr.ecr.us-east-1.amazonaws.com/recipe-app-backend:midpoint-v1
```

**Not yet complete:** persistent SQLite configuration, secure runtime secrets, database migrations, container startup, and remote API testing. The current Docker image's default database storage should not be assumed persistent across container replacement.

## 7. Updating infrastructure

1. Edit the appropriate CloudFormation template.
2. Validate the template.
3. Review the proposed changes (use CloudFormation change sets for important updates).
4. Deploy the stack.
5. Verify stack outputs and resource health.
6. Update this README and architecture documentation.

Avoid manual changes to CloudFormation-managed resources because they can cause configuration drift.

### Troubleshooting failed stack creation

A stack in `ROLLBACK_COMPLETE` cannot be updated. Inspect the failure **before** deleting it:

```bash
aws cloudformation describe-stack-events \
  --stack-name recipe-app-backend \
  --region us-east-1 \
  --profile recipe-app \
  --query "StackEvents[?ResourceStatus=='CREATE_FAILED'].[Timestamp,LogicalResourceId,ResourceStatusReason]" \
  --output table
```

During the initial backend deployment, `t3.micro` was unavailable in the original subnet's Availability Zone (`us-east-1e`). A second subnet in `us-east-1a` resolved this issue.

## 8. Planned improvements

- Run the Django/Gunicorn container from ECR on EC2 with persistent storage and environment-based secrets.
- Expose the API through a controlled HTTPS endpoint; do not expose Django administration or SSH unnecessarily.
- Replace temporary SQLite storage with a managed database such as Amazon RDS.
- Host the React frontend using Amazon S3 and CloudFront.
- Add automated builds and deployments (CI/CD).
- Evaluate private subnets, load balancing, Auto Scaling, multiple EC2 instances, and CloudWatch alarms for security, resilience, and scalability.

An architecture diagram documenting VPC CIDRs, subnets, routing, EC2 placement, security boundaries, and future database connectivity is planned.

## 9. Security and cost notes

- Use IAM Identity Center and short-lived credentials for developer access.
- Never commit AWS keys, Django secret keys, or other secrets.
- Keep ECR pull permissions scoped to the backend repository.
- Keep inbound security group access closed until a deliberate API exposure design is in place.
- Prefer Session Manager over public SSH access.
- EC2, EBS, public IPv4 addresses, ECR storage, and data transfer may incur AWS charges while resources exist.
- Use the deployed CloudFormation outputs as the source of truth for instance IDs and addresses.

## 10. Cleanup (destructive)

> **Warning:** Stack deletion can remove infrastructure and application data. Back up data and confirm team approval before cleanup. Do not run these commands against active resources.

The backend stack imports resources from the network and ECR stacks. Delete dependent stacks **before** deleting the network or registry stacks. An ECR repository containing images may block stack deletion unless images are removed first; the template intentionally sets `EmptyOnDelete: false`.

```bash
# Delete the backend stack first.
aws cloudformation delete-stack \
  --stack-name recipe-app-backend \
  --region us-east-1 \
  --profile recipe-app

aws cloudformation wait stack-delete-complete \
  --stack-name recipe-app-backend \
  --region us-east-1 \
  --profile recipe-app

# Only after dependent resources are removed:
aws cloudformation delete-stack \
  --stack-name recipe-app-network \
  --region us-east-1 \
  --profile recipe-app

aws cloudformation wait stack-delete-complete \
  --stack-name recipe-app-network \
  --region us-east-1 \
  --profile recipe-app
```

The ECR stack requires separate cleanup after its images and cross-stack dependencies have been handled. No cleanup is necessary during active development.
