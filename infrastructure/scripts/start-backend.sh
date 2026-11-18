#!/bin/bash
set -euo pipefail

# Discover AWS region and account from the EC2 instance identity.
# IMDSv2 is required by the launch template.
TOKEN=$(curl -fsS -X PUT \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" \
  http://169.254.169.254/latest/api/token)

IDENTITY=$(curl -fsS \
  -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/dynamic/instance-identity/document)

REGION=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["region"])' <<< "$IDENTITY")
ACCOUNT_ID=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["accountId"])' <<< "$IDENTITY")

REGISTRY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

# Deployment-specific settings are published to Parameter Store.
CONFIG_PREFIX="/recipe-app/production"

get_config() {
  aws ssm get-parameter \
    --name "${CONFIG_PREFIX}/$1" \
    --region "$REGION" \
    --query 'Parameter.Value' \
    --output text
}

ECR_REPOSITORY=$(get_config "ecr-repository")
ECR_IMAGE_TAG=$(get_config "ecr-image-tag")

IMAGE="${REGISTRY}/${ECR_REPOSITORY}:${ECR_IMAGE_TAG}"

DJANGO_SECRET_ARN=$(get_config "django-secret-arn")
RDS_SECRET_ARN=$(get_config "rds-secret-arn")

DB_HOST=$(get_config "db-host")
DB_NAME=$(get_config "db-name")
DB_PORT=$(get_config "db-port")

MEDIA_BUCKET=$(get_config "media-bucket")
CLOUDFRONT_DOMAIN=$(get_config "cloudfront-domain")
ALB_DOMAIN=$(get_config "alb-domain")

COGNITO_USER_POOL_ID=$(get_config "cognito-user-pool-id")
COGNITO_APP_CLIENT_ID=$(get_config "cognito-client-id")

ENV_FILE="/opt/recipe-app/backend.env"

echo "[1/4] Retrieving application secrets..."

DJANGO_SECRET=$(aws secretsmanager get-secret-value \
  --secret-id "$DJANGO_SECRET_ARN" \
  --region "$REGION" \
  --query SecretString \
  --output text)

RDS_SECRET=$(aws secretsmanager get-secret-value \
  --secret-id "$RDS_SECRET_ARN" \
  --region "$REGION" \
  --query SecretString \
  --output text)

echo "[2/4] Preparing environment configuration..."

umask 077
export DJANGO_SECRET RDS_SECRET ENV_FILE
export REGION DB_HOST DB_NAME DB_PORT
export MEDIA_BUCKET CLOUDFRONT_DOMAIN ALB_DOMAIN
export COGNITO_USER_POOL_ID COGNITO_APP_CLIENT_ID

python3 - <<'PY'
import json
import os
from pathlib import Path

django = json.loads(os.environ["DJANGO_SECRET"])
rds = json.loads(os.environ["RDS_SECRET"])

settings = {
    "DJANGO_SECRET_KEY": django["DJANGO_SECRET_KEY"],
    "DJANGO_DEBUG": "False",
    "DJANGO_ALLOWED_HOSTS": ",".join([
        "localhost",
        "127.0.0.1",
        os.environ["CLOUDFRONT_DOMAIN"],
        os.environ["ALB_DOMAIN"],
    ]),
    "DB_ENGINE": "postgresql",
    "DB_NAME": os.environ["DB_NAME"],
    "DB_USER": rds["username"],
    "DB_PASSWORD": rds["password"],
    "DB_HOST": os.environ["DB_HOST"],
    "DB_PORT": os.environ["DB_PORT"],
    "DB_SSLMODE": "verify-full",
    "DB_SSL_ROOT_CERT": "/app/certs/rds-global-bundle.pem",
    "MEDIA_STORAGE_BACKEND": "s3",
    "AWS_MEDIA_BUCKET_NAME": os.environ["MEDIA_BUCKET"],
    "AWS_MEDIA_CLOUDFRONT_DOMAIN": os.environ["CLOUDFRONT_DOMAIN"],
    "AWS_REGION": os.environ["REGION"],
    "COGNITO_REGION": os.environ["REGION"],
    "COGNITO_USER_POOL_ID": os.environ["COGNITO_USER_POOL_ID"],
    "COGNITO_APP_CLIENT_IDS": os.environ["COGNITO_APP_CLIENT_ID"],
}

def docker_env_value(value):
    value = str(value)
    if "\n" in value or "\r" in value:
        raise ValueError("Multiline environment values are not supported")
    return value

path = Path(os.environ["ENV_FILE"])
with path.open("w") as file:
    for key, value in settings.items():
        file.write(f"{key}={docker_env_value(value)}\n")

path.chmod(0o600)
print("Environment file created.")
PY

unset DJANGO_SECRET RDS_SECRET

echo "[3/4] Authenticating with Amazon ECR..."

aws ecr get-login-password --region "$REGION" \
  | docker login --username AWS --password-stdin "$REGISTRY"

docker pull "$IMAGE"

echo "[4/4] Starting Django container..."

docker rm -f recipe-app-backend 2>/dev/null || true

docker run -d \
  --name recipe-app-backend \
  --restart unless-stopped \
  --env-file "$ENV_FILE" \
  -p 127.0.0.1:8000:8000 \
  "$IMAGE"

echo "Waiting for Django to become available..."

for attempt in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8000/api/recipes/ >/dev/null; then
    echo "Backend container started and Django is responding."
    exit 0
  fi

  if ! docker inspect \
    --format '{{.State.Running}}' \
    recipe-app-backend 2>/dev/null | grep -qx true; then
    echo "Backend container is not running." >&2
    docker logs --tail 100 recipe-app-backend >&2 || true
    exit 1
  fi

  sleep 2
done

echo "ERROR: Django did not become available within 60 seconds." >&2
docker logs --tail 100 recipe-app-backend >&2
exit 1