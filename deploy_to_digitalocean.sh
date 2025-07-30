#!/bin/bash

# Discord Bot Deployment Script for DigitalOcean
# This script automates the deployment of the Discord Media Bot to a fresh Ubuntu droplet

set -e  # Exit on error

echo "=== Discord Media Bot Deployment Script ==="
echo "Starting deployment to DigitalOcean..."

# Function to wait for apt lock
wait_for_apt() {
    while fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do
        echo "Waiting for apt lock to be released..."
        sleep 5
    done
}

# Step 1: Update system
echo "Step 1: Updating system packages..."
wait_for_apt
apt update && apt upgrade -y

# Step 2: Install required software
echo "Step 2: Installing Python, Git, and FFmpeg..."
wait_for_apt
apt install -y python3 python3-pip python3-venv git ffmpeg

# Step 3: Create bot user
echo "Step 3: Creating bot user..."
if ! id -u botuser > /dev/null 2>&1; then
    adduser botuser --disabled-password --gecos ""
    echo "User 'botuser' created"
else
    echo "User 'botuser' already exists"
fi

# Step 4: Clone repository as botuser
echo "Step 4: Setting up bot code..."
su - botuser << 'EOF'
# Remove existing directory if it exists
if [ -d "discord-media-bot" ]; then
    echo "Removing existing discord-media-bot directory..."
    rm -rf discord-media-bot
fi

# Clone the repository
echo "Cloning repository..."
git clone https://github.com/MalachiMindwyre/discord-media-bot.git || {
    echo "Failed to clone repository. Please check if the repository is public."
    exit 1
}
cd discord-media-bot

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Bot code setup complete!"
EOF

# Step 5: Create systemd service
echo "Step 5: Creating systemd service..."
cat > /etc/systemd/system/discord-bot.service << 'SERVICE'
[Unit]
Description=Discord Media Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/home/botuser/discord-media-bot
Environment="PATH=/home/botuser/discord-media-bot/venv/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/home/botuser/discord-media-bot/venv/bin/python /home/botuser/discord-media-bot/discord-media-bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

# Step 6: Set up firewall
echo "Step 6: Setting up firewall..."
ufw allow OpenSSH
echo "y" | ufw enable

# Step 7: Enable service
echo "Step 7: Enabling bot service..."
systemctl daemon-reload
systemctl enable discord-bot

echo ""
echo "=== DEPLOYMENT ALMOST COMPLETE ==="
echo ""
echo "IMPORTANT: You need to add your Discord token!"
echo ""
echo "1. Create the .env file:"
echo "   echo 'DISCORD_TOKEN=YOUR_TOKEN_HERE' > /home/botuser/discord-media-bot/.env"
echo "   chmod 600 /home/botuser/discord-media-bot/.env"
echo "   chown botuser:botuser /home/botuser/discord-media-bot/.env"
echo ""
echo "2. Start the bot:"
echo "   systemctl start discord-bot"
echo "   systemctl status discord-bot"
echo ""
echo "3. View logs:"
echo "   journalctl -u discord-bot -f"
echo ""
echo "Optional: Copy your bot_config.json to preserve settings"