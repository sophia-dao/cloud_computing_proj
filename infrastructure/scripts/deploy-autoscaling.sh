
#!/usr/bin/env bash
set -euo pipefail

EXPECTED_ACCOUNT_ID="${1:?Usage: deploy-autoscaling.sh AWS_ACCOUNT_ID}"

REGION="us-east-1"
STACK_NAME="recipe-app-autoscaling"
REPOSITORY="recipe-app-backend"
IMAGE_TAG="final-v1"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE="$ROOT/cloudformation/autoscaling-packaged.yaml"

for cmd in aws python3; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "ERROR: Missing required command: $cmd" >&2
    exit 1
  fi
done

# Verify AWS account
ACCOUNT_ID=$(aws sts get-caller-identity \
  --region "$REGION" \
  --query Account \
  --output text)

if [[ "$ACCOUNT_ID" != "$EXPECTED_ACCOUNT_ID" ]]; then
  echo "ERROR: AWS account mismatch." >&2
  exit 1
fi

# Verify backend image exists in ECR
IMAGE_COUNT=$(aws ecr describe-images \
  --repository-name "$REPOSITORY" \
  --image-ids imageTag="$IMAGE_TAG" \
  --region "$REGION" \
  --query 'length(imageDetails)' \
  --output text)

if [[ "$IMAGE_COUNT" != "1" ]]; then
  echo "ERROR: Backend image $REPOSITORY:$IMAGE_TAG not found." >&2
  exit 1
fi

# Prevent accidental updates to an existing stack
if aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" >/dev/null 2>&1; then
  echo "ERROR: Stack already exists: $STACK_NAME" >&2
  exit 1
fi

echo "Packaging Auto Scaling template..."

python3 "$ROOT/scripts/package-autoscaling.py"

if [[ ! -f "$TEMPLATE" ]]; then
  echo "ERROR: Packaged template not found." >&2
  exit 1
fi

echo
echo "Account: $ACCOUNT_ID"
echo "Region:  $REGION"
echo "Stack:   $STACK_NAME"
echo "Image:   $REPOSITORY:$IMAGE_TAG"
echo "Mode:    Initial deployment (1 EC2 instance)"
echo

read -r -p "Type DEPLOY to continue: " CONFIRM

if [[ "$CONFIRM" != "DEPLOY" ]]; then
  echo "Cancelled."
  exit 1
fi

aws cloudformation deploy \
  --stack-name "$STACK_NAME" \
  --template-file "$TEMPLATE" \
  --region "$REGION" \
  --parameter-overrides InitialDeployment=true \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM

echo
echo "Auto Scaling stack deployed."
echo "Waiting for Systems Manager connectivity..."

ASG_NAME=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='AutoScalingGroupName'].OutputValue | [0]" \
  --output text)

for attempt in $(seq 1 60); do
  INSTANCE_ID=$(aws autoscaling describe-auto-scaling-groups \
    --auto-scaling-group-names "$ASG_NAME" \
    --region "$REGION" \
    --query "AutoScalingGroups[0].Instances[?LifecycleState=='InService'].InstanceId | [0]" \
    --output text)

  if [[ -n "$INSTANCE_ID" && "$INSTANCE_ID" != "None" ]]; then
    STATUS=$(aws ssm describe-instance-information \
      --region "$REGION" \
      --filters "Key=InstanceIds,Values=$INSTANCE_ID" \
      --query "InstanceInformationList[0].PingStatus" \
      --output text)

    if [[ "$STATUS" == "Online" ]]; then
      echo "EC2 instance is online in Systems Manager."
      echo "Instance ID: $INSTANCE_ID"
      echo
      echo "Next: Run initialize-database.sh"
      exit 0
    fi
  fi

  echo "Waiting for EC2 / SSM... ($attempt/60)"
  sleep 10
done

echo "WARNING: Instance did not become SSM Online within 10 minutes."
echo "Check EC2, Systems Manager, and CloudFormation."
exit 1
