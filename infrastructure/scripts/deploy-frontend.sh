
#!/usr/bin/env bash
set -euo pipefail

# Usage: ./infrastructure/scripts/deploy-frontend.sh AWS_ACCOUNT_ID
EXPECTED_ACCOUNT_ID="${1:?Usage: deploy-frontend.sh AWS_ACCOUNT_ID}"
REGION="us-east-1"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FRONTEND_DIR="$ROOT/frontend"

# Verify AWS account
ACCOUNT_ID=$(aws sts get-caller-identity \
  --query Account --output text)

if [[ "$ACCOUNT_ID" != "$EXPECTED_ACCOUNT_ID" ]]; then
  echo "ERROR: AWS account mismatch." >&2
  exit 1
fi

# Read CloudFormation exports
get_export() {
  local name="$1"
  local value

  value=$(aws cloudformation list-exports \
    --region "$REGION" \
    --query "Exports[?Name=='${name}'].Value | [0]" \
    --output text)

  if [[ -z "$value" || "$value" == "None" ]]; then
    echo "ERROR: Missing CloudFormation export: $name" >&2
    exit 1
  fi

  printf '%s\n' "$value"
}

CF_DOMAIN=$(get_export "RecipeApp-CloudFrontDomainName")
CF_DISTRIBUTION=$(get_export "RecipeApp-CloudFrontDistributionId")
FRONTEND_BUCKET=$(get_export "RecipeApp-FrontendBucketName")
COGNITO_DOMAIN=$(get_export "RecipeApp-CognitoDomain")
COGNITO_CLIENT_ID=$(get_export "RecipeApp-CognitoClientId")

FRONTEND_URL="https://${CF_DOMAIN}"

echo "AWS account: $ACCOUNT_ID"
echo "Frontend:    $FRONTEND_URL"
echo "S3 bucket:   $FRONTEND_BUCKET"

read -r -p "Type DEPLOY to build and upload the frontend: " CONFIRM

if [[ "$CONFIRM" != "DEPLOY" ]]; then
  echo "Cancelled."
  exit 0
fi

# Create temporary production environment configuration.
# Vite loads .env.production.local during npm run build.
ENV_FILE="$FRONTEND_DIR/.env.production.local"

if [[ -e "$ENV_FILE" ]]; then
  echo "ERROR: $ENV_FILE already exists." >&2
  echo "Remove or back it up manually before continuing." >&2
  exit 1
fi

cleanup() {
  rm -f "$ENV_FILE"
}
trap cleanup EXIT

cat > "$ENV_FILE" <<EOF
VITE_API_BASE_URL=${FRONTEND_URL}/api
VITE_DEV_BASIC_AUTH=
VITE_COGNITO_DOMAIN=${COGNITO_DOMAIN}
VITE_COGNITO_CLIENT_ID=${COGNITO_CLIENT_ID}
VITE_COGNITO_REDIRECT_URI=${FRONTEND_URL}/auth/callback
VITE_COGNITO_LOGOUT_URI=${FRONTEND_URL}/
VITE_COGNITO_SCOPES=openid email profile
VITE_COGNITO_GOOGLE_PROVIDER=Google
EOF

echo "Building React frontend..."

cd "$FRONTEND_DIR"
npm ci
npm run build

echo "Uploading frontend to S3..."

aws s3 sync dist/ "s3://${FRONTEND_BUCKET}/" \
  --delete \
  --region "$REGION"

echo "Invalidating CloudFront cache..."

INVALIDATION_ID=$(aws cloudfront create-invalidation \
  --distribution-id "$CF_DISTRIBUTION" \
  --paths "/*" \
  --query "Invalidation.Id" \
  --output text)

echo "Frontend deployment submitted successfully."
echo "URL: $FRONTEND_URL"
echo "CloudFront invalidation: $INVALIDATION_ID"
