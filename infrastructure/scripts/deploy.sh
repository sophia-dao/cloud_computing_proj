
#!/usr/bin/env bash
set -euo pipefail

REGION="us-east-1"
EXPECTED_ACCOUNT_ID="${1:?Usage: deploy.sh AWS_ACCOUNT_ID}"
STACK_PREFIX="recipe-app"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATES="$ROOT/cloudformation"

command -v aws >/dev/null || {
  echo "AWS CLI is required." >&2
  exit 1
}

command -v python3 >/dev/null || {
  echo "Python 3 is required." >&2
  exit 1
}

for template in \
  network.yaml endpoints.yaml alb.yaml ecr.yaml \
  secrets.yaml media.yaml backend.yaml rds.yaml \
  database-access.yaml frontend.yaml media-policy.yaml \
  cognito.yaml config.yaml; do

  if [[ ! -f "$TEMPLATES/$template" ]]; then
    echo "ERROR: Missing template: $template" >&2
    exit 1
  fi
done

ACTUAL_ACCOUNT_ID=$(aws sts get-caller-identity \
  --region "$REGION" \
  --query Account \
  --output text)

if [[ "$ACTUAL_ACCOUNT_ID" != "$EXPECTED_ACCOUNT_ID" ]]; then
  echo "ERROR: AWS account mismatch." >&2
  echo "Expected: $EXPECTED_ACCOUNT_ID" >&2
  echo "Current:  $ACTUAL_ACCOUNT_ID" >&2
  exit 1
fi

echo "AWS account: $ACTUAL_ACCOUNT_ID"
echo "AWS region:  $REGION"
echo "Stack prefix: $STACK_PREFIX"
echo

read -r -p "Type DEPLOY to continue: " CONFIRMATION

if [[ "$CONFIRMATION" != "DEPLOY" ]]; then
  echo "Deployment cancelled."
  exit 1
fi

deploy_stack() {
  local name="$1"
  local template="$2"
  local stack_name="${STACK_PREFIX}-${name}"

  echo
  echo "===================================="
  echo "Deploying: $stack_name"
  echo "Template:  $template"
  echo "===================================="

  # This workflow is intended for a fresh account.
  # Do not update an existing stack automatically.
  if aws cloudformation describe-stacks \
    --stack-name "$stack_name" \
    --region "$REGION" >/dev/null 2>&1; then
    echo "ERROR: Stack already exists: $stack_name" >&2
    exit 1
  fi

  aws cloudformation deploy \
    --stack-name "$stack_name" \
    --template-file "$TEMPLATES/$template" \
    --region "$REGION" \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
    --no-fail-on-empty-changeset

  echo "Completed: $stack_name"
}

deploy_stack network network.yaml
deploy_stack endpoints endpoints.yaml
deploy_stack alb alb.yaml
deploy_stack ecr ecr.yaml
deploy_stack secrets secrets.yaml
deploy_stack media media.yaml
deploy_stack backend backend.yaml
deploy_stack rds rds.yaml
deploy_stack database-access database-access.yaml
deploy_stack frontend frontend.yaml
deploy_stack media-policy media-policy.yaml
deploy_stack cognito cognito.yaml
deploy_stack config config.yaml

echo
echo "===================================="
echo "Infrastructure deployment completed."
echo "===================================="
echo
echo "AWS account: $ACTUAL_ACCOUNT_ID"
echo "AWS region:  $REGION"
echo
echo "Next steps:"
echo "1. Build and push backend Docker image to ECR."
echo "2. Package the Auto Scaling CloudFormation template."
echo "3. Deploy Auto Scaling in initialization mode."
echo "4. Run database migrations and import recipes."
echo "5. Restore Auto Scaling desired capacity to 2."
echo "6. Build and deploy React frontend to S3."
echo "7. Verify application through CloudFront."