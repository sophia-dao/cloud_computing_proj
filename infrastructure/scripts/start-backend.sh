#!/bin/bash
set -euo pipefail

REGION="us-east-1"
IMAGE="362176666546.dkr.ecr.us-east-1.amazonaws.com/recipe-app-backend:search-v1"
REGISTRY="362176666546.dkr.ecr.us-east-1.amazonaws.com"

DJANGO_SECRET_ARN="arn:aws:secretsmanager:us-east-1:362176666546:secret:recipe-app/production/django-oEYU9L"
RDS_SECRET_ARN="arn:aws:secretsmanager:us-east-1:362176666546:secret:rds!db-a10bf540-1d22-4409-978a-31ff85c44a7c-5xpOFJ"

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

python3 - <<'PY'
import json
import os
from pathlib import Path

django = json.loads(os.environ["DJANGO_SECRET"])
rds = json.loads(os.environ["RDS_SECRET"])

settings = {
    "DJANGO_SECRET_KEY": django["DJANGO_SECRET_KEY"],
    "DJANGO_DEBUG": "False",
    "DJANGO_ALLOWED_HOSTS": (
        "localhost,127.0.0.1,"
        "internal-recipe-app-internal-alb-1524514520.us-east-1.elb.amazonaws.com"
    ),
    "DB_ENGINE": "postgresql",
    "DB_NAME": "recipe_app",
    "DB_USER": rds["username"],
    "DB_PASSWORD": rds["password"],
    "DB_HOST": "recipe-app-postgres.c41i64gcemdw.us-east-1.rds.amazonaws.com",
    "DB_PORT": "5432",
    "DB_SSLMODE": "verify-full",
    "DB_SSL_ROOT_CERT": "/app/certs/rds-global-bundle.pem",
    "MEDIA_STORAGE_BACKEND": "s3",
    "AWS_MEDIA_BUCKET_NAME": "recipe-app-media-mediabucket-w0ts6zix1yiu",
    "AWS_MEDIA_CLOUDFRONT_DOMAIN": "d1q0iv2raorz8j.cloudfront.net",
    "AWS_REGION": "us-east-1",
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

echo "Backend container started."
sh-5.2$ sudo cat /opt/recipe-app/start-backend.sh
#!/bin/bash
set -euo pipefail

REGION="us-east-1"
IMAGE="362176666546.dkr.ecr.us-east-1.amazonaws.com/recipe-app-backend:search-v1"
REGISTRY="362176666546.dkr.ecr.us-east-1.amazonaws.com"

DJANGO_SECRET_ARN="arn:aws:secretsmanager:us-east-1:362176666546:secret:recipe-app/production/django-oEYU9L"
RDS_SECRET_ARN="arn:aws:secretsmanager:us-east-1:362176666546:secret:rds!db-a10bf540-1d22-4409-978a-31ff85c44a7c-5xpOFJ"

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

python3 - <<'PY'
import json
import os
from pathlib import Path

django = json.loads(os.environ["DJANGO_SECRET"])
rds = json.loads(os.environ["RDS_SECRET"])

settings = {
    "DJANGO_SECRET_KEY": django["DJANGO_SECRET_KEY"],
    "DJANGO_DEBUG": "False",
    "DJANGO_ALLOWED_HOSTS": (
        "localhost,127.0.0.1,"
        "internal-recipe-app-internal-alb-1524514520.us-east-1.elb.amazonaws.com"
    ),
    "DB_ENGINE": "postgresql",
    "DB_NAME": "recipe_app",
    "DB_USER": rds["username"],
    "DB_PASSWORD": rds["password"],
    "DB_HOST": "recipe-app-postgres.c41i64gcemdw.us-east-1.rds.amazonaws.com",
    "DB_PORT": "5432",
    "DB_SSLMODE": "verify-full",
    "DB_SSL_ROOT_CERT": "/app/certs/rds-global-bundle.pem",
    "MEDIA_STORAGE_BACKEND": "s3",
    "AWS_MEDIA_BUCKET_NAME": "recipe-app-media-mediabucket-w0ts6zix1yiu",
    "AWS_MEDIA_CLOUDFRONT_DOMAIN": "d1q0iv2raorz8j.cloudfront.net",
    "AWS_REGION": "us-east-1",
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

echo "Backend container started."