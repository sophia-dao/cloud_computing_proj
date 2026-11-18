
#!/usr/bin/env bash
set -euo pipefail

EXPECTED_ACCOUNT_ID="${1:?Usage: finalize-autoscaling.sh AWS_ACCOUNT_ID}"
REGION="us-east-1"
STACK_NAME="recipe-app-autoscaling"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEMPLATE="$ROOT/cloudformation/autoscaling-packaged.yaml"

ACCOUNT_ID=$(aws sts get-caller-identity \
  --region "$REGION" \
  --query Account --output text)

if [[ "$ACCOUNT_ID" != "$EXPECTED_ACCOUNT_ID" ]]; then
  echo "ERROR: AWS account mismatch." >&2
  exit 1
fi

if [[ ! -f "$TEMPLATE" ]]; then
  echo "ERROR: Packaged Auto Scaling template missing." >&2
  exit 1
fi

# Ensure the stack already exists.
aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" >/dev/null

echo "Account: $ACCOUNT_ID"
echo "Stack:   $STACK_NAME"
echo "Action:  Restore 2 backend instances"
echo

read -r -p "Type FINALIZE to continue: " CONFIRM

if [[ "$CONFIRM" != "FINALIZE" ]]; then
  echo "Cancelled."
  exit 1
fi

aws cloudformation deploy \
  --stack-name "$STACK_NAME" \
  --template-file "$TEMPLATE" \
  --region "$REGION" \
  --parameter-overrides InitialDeployment=false \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM

ASG_NAME=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='AutoScalingGroupName'].OutputValue | [0]" \
  --output text)

echo "Waiting for two healthy EC2 instances..."

for attempt in $(seq 1 60); do
  HEALTHY_COUNT=$(aws autoscaling describe-auto-scaling-groups \
    --auto-scaling-group-names "$ASG_NAME" \
    --region "$REGION" \
    --query "length(AutoScalingGroups[0].Instances[?LifecycleState=='InService' && HealthStatus=='Healthy'])" \
    --output text)

  if [[ "$HEALTHY_COUNT" -ge 2 ]]; then
    echo "Auto Scaling finalized: $HEALTHY_COUNT healthy instances."
    exit 0
  fi

  echo "Waiting... ($attempt/60)"
  sleep 10
done

echo "WARNING: Two healthy instances not confirmed within 10 minutes."
exit 1
