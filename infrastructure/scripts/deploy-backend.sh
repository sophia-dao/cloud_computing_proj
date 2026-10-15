#!/usr/bin/env bash
# Deploy the Django backend container from ECR onto the existing EC2 instance
# using SSM Run Command (no SSH, no inbound port needed for the deploy itself).
#
# Usage (from the repository root):
#   AWS_PROFILE=recipe-app IMAGE_TAG=midpoint-v2 ./infrastructure/scripts/deploy-backend.sh
#
# Environment:
#   AWS_PROFILE    local AWS CLI profile            (default: recipe-app)
#   AWS_REGION     region                           (default: us-east-1)
#   IMAGE_TAG      ECR image tag to run             (default: midpoint-v1)
#   STACK_NAME     backend CloudFormation stack     (default: recipe-app-backend)
#   SEED_DEMO_DATA 1 to insert a few demo ingredients if missing (default: 1)
#
# The Django secret key is generated ON the instance the first time and kept in
# /opt/recipe-app/backend.env (root-only). It never leaves the instance and is
# never committed to the repository.

set -euo pipefail
export MSYS_NO_PATHCONV=1  # stop Git Bash on Windows from rewriting arguments

AWS_PROFILE="${AWS_PROFILE:-recipe-app}"
AWS_REGION="${AWS_REGION:-us-east-1}"
IMAGE_TAG="${IMAGE_TAG:-midpoint-v1}"
STACK_NAME="${STACK_NAME:-recipe-app-backend}"
SEED_DEMO_DATA="${SEED_DEMO_DATA:-1}"
REPOSITORY="recipe-app-backend"
CONTAINER="recipe-app-backend"
API_PORT=8000

aws_() { aws --profile "$AWS_PROFILE" --region "$AWS_REGION" "$@"; }

stack_output() {
  aws_ cloudformation describe-stacks --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text
}

INSTANCE_ID="$(stack_output InstanceId)"
ACCOUNT_ID="$(aws_ sts get-caller-identity --query Account --output text)"
# Read the live IP instead of the stack output: it changes after stop/start.
PUBLIC_IP="$(aws_ ec2 describe-instances --instance-ids "$INSTANCE_ID" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)"
REGISTRY="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
IMAGE="$REGISTRY/$REPOSITORY:$IMAGE_TAG"

echo "Instance : $INSTANCE_ID ($PUBLIC_IP)"
echo "Image    : $IMAGE"

# ---------------------------------------------------------------------------
# Script executed on the EC2 instance (as root) by SSM.
# ---------------------------------------------------------------------------
REMOTE_SCRIPT=$(cat <<EOF
set -euo pipefail

aws ecr get-login-password --region $AWS_REGION \
  | docker login --username AWS --password-stdin $REGISTRY
docker pull $IMAGE

mkdir -p /opt/recipe-app/data
if [ ! -f /opt/recipe-app/backend.env ]; then
  umask 077
  echo "DJANGO_SECRET_KEY=\$(head -c 48 /dev/urandom | od -An -tx1 | tr -d ' \n')" \
    > /opt/recipe-app/backend.env
  echo "Generated new Django secret key on instance"
fi

docker rm -f $CONTAINER 2>/dev/null || true

# Migrate inside the serving container so it also works with images whose
# SQLite file lives inside the container (midpoint-v1). Images built after
# DJANGO_SQLITE_PATH was added store the database on the host volume instead.
docker run -d --name $CONTAINER --restart unless-stopped \
  -p $API_PORT:8000 \
  --env-file /opt/recipe-app/backend.env \
  -e DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,$PUBLIC_IP \
  -e DJANGO_SQLITE_PATH=/data/db.sqlite3 \
  -v /opt/recipe-app/data:/data \
  $IMAGE \
  sh -c 'python manage.py migrate --noinput && exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --access-logfile - --error-logfile -'

for i in \$(seq 1 30); do
  if curl -fsS http://localhost:$API_PORT/api/health/ >/dev/null 2>&1; then break; fi
  sleep 2
done

if [ "$SEED_DEMO_DATA" = "1" ]; then
  docker exec $CONTAINER python manage.py shell -c "
from apps.ingredients.models import Ingredient
demo = [('Chicken Breast', 'Protein'), ('Egg', 'Protein'), ('Rice', 'Grain'),
        ('Tomato', 'Vegetable'), ('Onion', 'Vegetable'), ('Garlic', 'Vegetable'),
        ('Olive Oil', 'Oil'), ('Cheddar Cheese', 'Dairy'), ('Pasta', 'Grain'),
        ('Spinach', 'Vegetable')]
added = 0
for name, category in demo:
    if not Ingredient.objects.filter(name__iexact=name).exists():
        Ingredient.objects.create(name=name, category=category)
        added += 1
print(f'Seeded {added} demo ingredients')
"
fi

echo '--- docker ps'
docker ps --filter name=$CONTAINER
echo '--- GET /api/health/'
curl -fsS http://localhost:$API_PORT/api/health/ \
  || { echo 'Health check failed; container logs:'; docker logs --tail 80 $CONTAINER; exit 1; }
echo
echo '--- GET /api/ingredients/?search=to'
curl -fsS "http://localhost:$API_PORT/api/ingredients/?search=to"; echo
EOF
)

ENCODED="$(printf '%s' "$REMOTE_SCRIPT" | base64 | tr -d '\n')"

COMMAND_ID="$(aws_ ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name AWS-RunShellScript \
  --comment "Deploy $REPOSITORY:$IMAGE_TAG" \
  --parameters "{\"commands\":[\"echo $ENCODED | base64 -d > /tmp/deploy-backend.sh && bash /tmp/deploy-backend.sh\"],\"executionTimeout\":[\"900\"]}" \
  --query Command.CommandId --output text)"

echo "SSM command: $COMMAND_ID (waiting for it to finish...)"

STATUS=Pending
for _ in $(seq 1 180); do
  STATUS="$(aws_ ssm get-command-invocation --command-id "$COMMAND_ID" \
    --instance-id "$INSTANCE_ID" --query Status --output text 2>/dev/null || echo Pending)"
  case "$STATUS" in Pending|InProgress|Delayed) sleep 5 ;; *) break ;; esac
done

echo "--- remote stdout"
aws_ ssm get-command-invocation --command-id "$COMMAND_ID" --instance-id "$INSTANCE_ID" \
  --query StandardOutputContent --output text
echo "--- remote stderr"
aws_ ssm get-command-invocation --command-id "$COMMAND_ID" --instance-id "$INSTANCE_ID" \
  --query StandardErrorContent --output text

echo "Status: $STATUS"
[ "$STATUS" = "Success" ] || exit 1

echo
echo "Deployed. From an allowed IP (see api-access.yaml) test:"
echo "  curl http://$PUBLIC_IP:$API_PORT/api/health/"
echo "  curl http://$PUBLIC_IP:$API_PORT/api/ingredients/"
