from pathlib import Path
import base64
import json
import re

ROOT = Path(__file__).resolve().parents[1]

startup_path = ROOT / "scripts" / "start-backend.sh"
bootstrap_path = ROOT / "scripts" / "bootstrap-backend.sh"
template_path = ROOT / "cloudformation" / "autoscaling.yaml"
output_path = ROOT / "cloudformation" / "autoscaling-packaged.yaml"

startup = startup_path.read_text(encoding="utf-8")
bootstrap = bootstrap_path.read_text(encoding="utf-8")
bootstrap_size = len(bootstrap.encode("utf-8"))

if bootstrap_size > 16 * 1024:
    raise ValueError(
        f"User Data exceeds EC2's 16 KiB raw limit: {bootstrap_size} bytes"
    )

template = template_path.read_text(encoding="utf-8")

placeholder = "__START_BACKEND_SCRIPT__"

if bootstrap.count(placeholder) != 1:
    raise ValueError("Expected exactly one startup script placeholder")

if "START_SCRIPT" in startup:
    raise ValueError("Startup script contains a conflicting heredoc delimiter")

bootstrap = bootstrap.replace(placeholder, startup.rstrip("\n"))

if "UserData:" in template:
    raise ValueError("Template already contains UserData")

if "SecurityGroupIds:" in template:
    raise ValueError("Remove duplicate SecurityGroupIds before packaging")

userdata = base64.b64encode(bootstrap.encode()).decode()

insertion = (
    "        UserData: " + json.dumps(userdata) + "\n"
)

pattern = r"(?m)^        MetadataOptions:"

if len(re.findall(pattern, template)) != 1:
    raise ValueError("Expected exactly one MetadataOptions block")

packaged = re.sub(
    pattern,
    insertion + "        MetadataOptions:",
    template,
    count=1,
)

output_path.write_text(packaged, encoding="utf-8")

print(f"Created: {output_path}")
print(f"Bootstrap size: {bootstrap_size} bytes")
print(f"Encoded User Data size: {len(userdata)} characters")