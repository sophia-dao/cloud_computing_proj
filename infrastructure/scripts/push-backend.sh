
#!/usr/bin/env bash
set -euo pipefail

EXPECTED_ACCOUNT_ID="${1:?Usage: push-backend.sh AWS_ACCOUNT_ID}"
REGION="us-east-1"
REPOSITORY="recipe-app-backend"
IMAGE_TAG="final-v1"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

for command in aws docker; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "ERROR: $command is required." >&2
    exit 1
  fi
done

if ! docker info >/dev/null 2>&1; then
  echo "ERROR: Docker is not running." >&2
  exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity \
  --region "$REGION" \
  --query Account \
  --output text)

if [[ "$ACCOUNT_ID" != "$EXPECTED_ACCOUNT_ID" ]]; then
  echo "ERROR: AWS account mismatch." >&2
  exit 1
fi

REGISTRY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
IMAGE="${REGISTRY}/${REPOSITORY}:${IMAGE_TAG}"

if ! aws ecr describe-repositories \
  --repository-names "$REPOSITORY" \
  --region "$REGION" >/dev/null 2>&1; then
  echo "ERROR: ECR repository '$REPOSITORY' not found." >&2
  echo "Deploy the ECR CloudFormation stack first." >&2
  exit 1
fi

echo "Account: $ACCOUNT_ID"
echo "Region:  $REGION"
echo "Image:   $IMAGE"

read -r -p "Type PUSH to continue: " CONFIRMATION

if [[ "$CONFIRMATION" != "PUSH" ]]; then
  echo "Cancelled."
  exit 1
fi

echo "Logging in to Amazon ECR..."

aws ecr get-login-password --region "$REGION" \
  | docker login \
      --username AWS \
      --password-stdin "$REGISTRY"

echo "Building backend Docker image..."

docker build \
  --platform linux/amd64 \
  -t "$IMAGE" \
  "$ROOT/backend"

echo "Pushing backend image..."

docker push "$IMAGE"

echo "Image successfully pushed:"
echo "$IMAGE"
