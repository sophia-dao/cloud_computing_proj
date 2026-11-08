#!/bin/bash
set -euo pipefail

echo "[Bootstrap] Starting Recipe App backend setup..."

# Ensure application directory exists
mkdir -p /opt/recipe-app

# Enable required services
systemctl enable --now docker
systemctl enable --now nginx

# Install the startup script
# This placeholder will be replaced during CloudFormation packaging.
cat > /opt/recipe-app/start-backend.sh <<'START_SCRIPT'
__START_BACKEND_SCRIPT__
START_SCRIPT

chmod 700 /opt/recipe-app/start-backend.sh

# Configure application-aware health check.
# ALB health checks use the target IP as the Host header.
# Proxy to Django with a trusted Host value.

python3 - <<'PY'
from pathlib import Path

path = Path("/etc/nginx/conf.d/recipe-app.conf")
config = path.read_text()

old = '''location = /healthz {
        default_type text/plain;
        access_log off;
        return 200 "ok\\n";
    }'''

new = '''location = /healthz {
        access_log off;

        proxy_pass http://127.0.0.1:8000/api/recipes/;
        proxy_set_header Host localhost;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 5s;
        proxy_read_timeout 10s;
    }'''

if config.count(old) != 1:
    raise SystemExit("Expected original Nginx health-check block not found")

path.write_text(config.replace(old, new))
print("[Bootstrap] Application health check configured")
PY

nginx -t
systemctl reload nginx

# Register systemd service
cat > /etc/systemd/system/recipe-app-backend.service <<'SERVICE'
[Unit]
Description=Recipe App Django Backend
Wants=network-online.target
After=network-online.target docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/opt/recipe-app/start-backend.sh
ExecStop=/usr/bin/docker stop recipe-app-backend
TimeoutStartSec=300
TimeoutStopSec=60
Restart=no

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable --now recipe-app-backend.service

echo "[Bootstrap] Recipe App backend setup completed."