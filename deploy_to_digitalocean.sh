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

# Step 5: Install screen
echo "Step 5: Installing screen..."
wait_for_apt
apt install -y screen

# Step 6: Create bot management script
echo "Step 6: Creating bot management script..."
cat > /home/botuser/manage_bots.sh << 'SCRIPT'
#!/bin/bash

case $1 in
  start)
    echo "Starting Discord bot in screen session..."
    cd /home/botuser/discord-media-bot
    screen -dmS media_bot bash -c 'source venv/bin/activate && python discord-media-bot.py'
    echo "Bot started! Use 'screen -r media_bot' to attach to session."
    ;;
  stop)
    echo "Stopping Discord bot..."
    screen -X -S media_bot quit 2>/dev/null
    echo "Bot stopped."
    ;;
  status)
    echo "Screen sessions:"
    screen -ls
    echo -e "\nRunning processes:"
    ps aux | grep -E 'discord-media-bot.py' | grep -v grep
    ;;
  *)
    echo "Usage: $0 {start|stop|status}"
    echo "  start  - Start bot in screen session"
    echo "  stop   - Stop bot"
    echo "  status - Show running session and process"
    ;;
esac
SCRIPT

chmod +x /home/botuser/manage_bots.sh
chown botuser:botuser /home/botuser/manage_bots.sh

# Step 7: Set up firewall
echo "Step 7: Setting up firewall..."
ufw allow OpenSSH
echo "y" | ufw enable

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
echo "   /home/botuser/manage_bots.sh start"
echo ""
echo "3. Check status:"
echo "   /home/botuser/manage_bots.sh status"
echo ""
echo "4. View logs (attach to screen):"
echo "   screen -r media_bot"
echo "   (Press Ctrl+A then D to detach)"
echo ""
echo "Optional: Copy your bot_config.json to preserve settings"