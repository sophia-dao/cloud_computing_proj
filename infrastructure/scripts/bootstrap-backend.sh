#!/bin/bash
set -euo pipefail

echo "[Bootstrap] Starting Recipe App backend setup..."

# Install required packages on Amazon Linux 2023
dnf install -y docker nginx python3

# Ensure application directory exists
mkdir -p /opt/recipe-app

# Enable Docker
systemctl enable --now docker

# Install the startup script
# This placeholder will be replaced during CloudFormation packaging.
cat > /opt/recipe-app/start-backend.sh <<'START_SCRIPT'
__START_BACKEND_SCRIPT__
START_SCRIPT

chmod 700 /opt/recipe-app/start-backend.sh

# Configure Nginx as the reverse proxy for Django/Gunicorn.
# ALB forwards HTTP requests to Nginx on port 80.

cat > /etc/nginx/conf.d/recipe-app.conf <<'NGINX'
server {
    listen 80;
    server_name _;

    location = /healthz {
        access_log off;

        proxy_pass http://127.0.0.1:8000/api/recipes/;
        proxy_set_header Host localhost;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 5s;
        proxy_read_timeout 10s;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 5s;
        proxy_read_timeout 60s;
    }
}
NGINX

# Validate Nginx configuration and start the service
nginx -t
systemctl enable --now nginx

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
ExecStop=-/usr/bin/docker stop recipe-app-backend
ExecStopPost=-/usr/bin/docker rm -f recipe-app-backend
TimeoutStartSec=600
TimeoutStopSec=60
Restart=no

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable --now recipe-app-backend.service

echo "[Bootstrap] Recipe App backend setup completed."