
#!/usr/bin/env bash
set -euo pipefail

EXPECTED_ACCOUNT_ID="${1:?Usage: initialize-database.sh AWS_ACCOUNT_ID}"
REGION="us-east-1"
STACK_NAME="recipe-app-autoscaling"

ACCOUNT_ID=$(aws sts get-caller-identity \
  --region "$REGION" \
  --query Account --output text)

if [[ "$ACCOUNT_ID" != "$EXPECTED_ACCOUNT_ID" ]]; then
  echo "ERROR: AWS account mismatch." >&2
  exit 1
fi

ASG_NAME=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='AutoScalingGroupName'].OutputValue | [0]" \
  --output text)

if [[ -z "$ASG_NAME" || "$ASG_NAME" == "None" ]]; then
  echo "ERROR: Auto Scaling Group not found." >&2
  exit 1
fi

INSTANCE_ID=$(aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names "$ASG_NAME" \
  --region "$REGION" \
  --query "AutoScalingGroups[0].Instances[?LifecycleState=='InService' && HealthStatus=='Healthy'].InstanceId | [0]" \
  --output text)

if [[ -z "$INSTANCE_ID" || "$INSTANCE_ID" == "None" ]]; then
  echo "ERROR: No healthy backend instance found." >&2
  exit 1
fi

echo "Account:  $ACCOUNT_ID"
echo "Region:   $REGION"
echo "ASG:      $ASG_NAME"
echo "Instance: $INSTANCE_ID"

SSM_STATUS=$(aws ssm describe-instance-information \
  --region "$REGION" \
  --filters "Key=InstanceIds,Values=$INSTANCE_ID" \
  --query "InstanceInformationList[0].PingStatus" \
  --output text)

if [[ "$SSM_STATUS" != "Online" ]]; then
  echo "ERROR: Instance is not online in Systems Manager." >&2
  exit 1
fi

read -r -p "Type INITIALIZE to continue: " CONFIRMATION

if [[ "$CONFIRMATION" != "INITIALIZE" ]]; then
  echo "Cancelled."
  exit 1
fi


echo "Running database initialization..."

# The remote command checks the existing recipe count.
# It skips importing if recipes are already present.
COMMANDS=$(python3 - <<'PY'
import json

commands = [
    "set -e",
    "docker inspect --format '{{.State.Running}}' recipe-app-backend | grep -qx true",
    "docker exec recipe-app-backend python manage.py migrate --noinput",
    """RECIPE_COUNT=$(docker exec recipe-app-backend python manage.py shell -c "from apps.recipes.models import Recipe; print(Recipe.objects.count())" | tail -n 1)""",
    'echo "Existing recipes: $RECIPE_COUNT"',
    """if [ "$RECIPE_COUNT" = "0" ]; then
  docker exec recipe-app-backend python manage.py import_themealdb --limit 100 --random
else
  echo "Recipes already exist. Skipping import."
fi""",
]

print(json.dumps({
    "commands": commands,
    "executionTimeout": ["3600"],
}))
PY
)

COMMAND_ID=$(aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --region "$REGION" \
  --comment "Initialize Recipe App database" \
  --parameters "$COMMANDS" \
  --timeout-seconds 600 \
  --query "Command.CommandId" \
  --output text)

echo "Command ID: $COMMAND_ID"
echo "Waiting for initialization to finish..."

# Poll until the command reaches a terminal state.
# The default AWS CLI waiter may stop too early.
for attempt in $(seq 1 240); do
  STATUS=$(aws ssm get-command-invocation \
    --command-id "$COMMAND_ID" \
    --instance-id "$INSTANCE_ID" \
    --region "$REGION" \
    --query Status \
    --output text 2>/dev/null || true)

  case "$STATUS" in
    Success)
      echo "Database initialization succeeded."
      break
      ;;
    Failed|Cancelled|TimedOut|Cancelling)
      echo "ERROR: Database initialization failed: $STATUS" >&2
      break
      ;;
    *)
      echo "Waiting for SSM command... ($attempt/240)"
      sleep 15
      ;;
  esac
done

echo
echo "Initialization results:"

aws ssm get-command-invocation \
  --command-id "$COMMAND_ID" \
  --instance-id "$INSTANCE_ID" \
  --region "$REGION" \
  --query '{Status:Status,ResponseCode:ResponseCode,Output:StandardOutputContent,Errors:StandardErrorContent}' \
  --output json

FINAL_STATUS=$(aws ssm get-command-invocation \
  --command-id "$COMMAND_ID" \
  --instance-id "$INSTANCE_ID" \
  --region "$REGION" \
  --query Status \
  --output text)

if [[ "$FINAL_STATUS" != "Success" ]]; then
  echo "ERROR: Database initialization did not succeed." >&2
  exit 1
fi

echo
echo "Database initialization completed successfully."