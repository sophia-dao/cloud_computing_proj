import copy
import difflib
import json
from pathlib import Path

backup_path = Path(
    "infrastructure/backups/cloudfront-before-vpc-origin.json"
)
output_path = Path(
    "infrastructure/backups/cloudfront-vpc-origin-candidate.json"
)
diff_path = Path(
    "infrastructure/backups/cloudfront-vpc-origin.diff"
)

backup = json.loads(backup_path.read_text())
original = backup["DistributionConfig"]
candidate = copy.deepcopy(original)

new_origin_id = "PrivateDjangoAPIOrigin"
old_origin_id = "DjangoAPIOrigin"

vpc_origin = {
    "Id": new_origin_id,
    "DomainName": (
        "internal-recipe-app-internal-alb-1524514520."
        "us-east-1.elb.amazonaws.com"
    ),
    "OriginPath": "",
    "CustomHeaders": {
        "Quantity": 0
    },
    "VpcOriginConfig": {
        "VpcOriginId": "vo_BE0O5HrJG2dFwrTMTCiYRQ",
        "OriginReadTimeout": 30,
        "OriginKeepaliveTimeout": 5
    },
    "ConnectionAttempts": 3,
    "ConnectionTimeout": 10
}

origins = candidate["Origins"]["Items"]

if any(origin["Id"] == new_origin_id for origin in origins):
    raise SystemExit("Private origin already exists")

origins.append(vpc_origin)
candidate["Origins"]["Quantity"] = len(origins)

api_behaviors = [
    behavior
    for behavior in candidate["CacheBehaviors"]["Items"]
    if behavior["PathPattern"] == "/api/*"
]

if len(api_behaviors) != 1:
    raise SystemExit("Expected exactly one /api/* behavior")

api_behavior = api_behaviors[0]

if api_behavior["TargetOriginId"] != old_origin_id:
    raise SystemExit("Unexpected existing API origin")

api_behavior["TargetOriginId"] = new_origin_id

output_path.write_text(
    json.dumps(candidate, indent=2) + "\n"
)

before = json.dumps(original, indent=2, sort_keys=True).splitlines()
after = json.dumps(candidate, indent=2, sort_keys=True).splitlines()

diff = difflib.unified_diff(
    before,
    after,
    fromfile="current-cloudfront",
    tofile="candidate-cloudfront",
    lineterm=""
)

diff_path.write_text("\n".join(diff) + "\n")

print("Candidate:", output_path)
print("Diff:", diff_path)
print("Original API origin preserved:", old_origin_id)
print("New API origin:", new_origin_id)
print("No AWS resources modified.")
