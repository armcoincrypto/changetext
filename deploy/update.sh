#!/usr/bin/env bash
set -euo pipefail

# === Quick update script ===
# Pull latest code and restart bot

APP_DIR="/opt/changetext"
SERVICE_NAME="changetext-bot"
BRANCH="claude/telegram-text-formatter-bot-qesQW"

cd "$APP_DIR"
echo "Pulling latest code..."
git pull origin "$BRANCH"

echo "Installing dependencies..."
pip3 install -r requirements.txt

echo "Restarting bot..."
systemctl restart "$SERVICE_NAME"

echo "Done! Checking status..."
systemctl status "$SERVICE_NAME" --no-pager
