#!/usr/bin/env bash
set -euo pipefail

# === changetext bot deploy script ===
# Usage: bash deploy/setup.sh

APP_DIR="/opt/changetext"
SERVICE_NAME="changetext-bot"
REPO_URL="git@github-changetext:armcoincrypto/changetext.git"
BRANCH="claude/telegram-text-formatter-bot-qesQW"

echo "=== changetext deploy ==="

# 1. SSH deploy key
if [ ! -f "$HOME/.ssh/changetext_deploy" ]; then
    echo "[1/6] Generating SSH deploy key..."
    ssh-keygen -t ed25519 -C "changetext-deploy" -f "$HOME/.ssh/changetext_deploy" -N ""
    echo ""
    echo ">>> Add this public key to GitHub as a Deploy Key:"
    echo ">>> Repo -> Settings -> Deploy keys -> Add deploy key"
    echo ">>> Title: changetext-deploy"
    echo ""
    cat "$HOME/.ssh/changetext_deploy.pub"
    echo ""
    read -rp "Press Enter after you've added the key to GitHub..."
else
    echo "[1/6] SSH deploy key already exists, skipping."
fi

# 2. SSH config
if ! grep -q "Host github-changetext" "$HOME/.ssh/config" 2>/dev/null; then
    echo "[2/6] Adding SSH config..."
    cat >> "$HOME/.ssh/config" << 'SSHEOF'

Host github-changetext
    HostName github.com
    User git
    IdentityFile ~/.ssh/changetext_deploy
    IdentitiesOnly yes
SSHEOF
    chmod 600 "$HOME/.ssh/config"
else
    echo "[2/6] SSH config already set, skipping."
fi

# 3. Clone or update repo
if [ ! -d "$APP_DIR/.git" ]; then
    echo "[3/6] Cloning repo..."
    git clone -b "$BRANCH" "$REPO_URL" "$APP_DIR"
else
    echo "[3/6] Updating repo..."
    cd "$APP_DIR"
    git fetch origin "$BRANCH"
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
fi

cd "$APP_DIR"

# 4. .env file
if [ ! -f "$APP_DIR/.env" ]; then
    echo "[4/6] Creating .env file..."
    read -rp "Enter your BOT_TOKEN: " token
    echo "BOT_TOKEN=$token" > "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"
else
    echo "[4/6] .env already exists, skipping."
fi

# 5. Install dependencies
echo "[5/6] Installing Python dependencies..."
pip3 install -r "$APP_DIR/requirements.txt"

# 6. Install and start systemd service
echo "[6/6] Setting up systemd service..."
cp "$APP_DIR/deploy/changetext-bot.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

echo ""
echo "=== Deploy complete! ==="
echo "  Status:  systemctl status $SERVICE_NAME"
echo "  Logs:    journalctl -u $SERVICE_NAME -f"
echo "  Restart: systemctl restart $SERVICE_NAME"
echo "  Stop:    systemctl stop $SERVICE_NAME"
