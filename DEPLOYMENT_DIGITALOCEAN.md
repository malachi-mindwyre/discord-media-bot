# Deploying Discord Media Bot to DigitalOcean

This guide walks you through deploying your Discord Media Bot to a DigitalOcean Droplet for 24/7 operation.

## Quick Start

### Prerequisites
- DigitalOcean account
- Discord bot token
- SSH key (optional but recommended)

### Step 1: Create Droplet
1. Log into DigitalOcean
2. Create Droplet with:
   - **Image**: Ubuntu 22.04 LTS
   - **Plan**: Basic ($6/month, 1GB RAM)
   - **Authentication**: SSH Key or Password
   - **Datacenter**: Choose closest location

### Step 2: Deploy Bot

#### Option A: Automated Script
```bash
# SSH into your droplet
ssh root@YOUR_DROPLET_IP

# Download and run deployment script
wget https://raw.githubusercontent.com/MalachiMindwyre/discord-media-bot/main/deploy_to_digitalocean.sh
chmod +x deploy_to_digitalocean.sh
./deploy_to_digitalocean.sh

# Add your Discord token
echo 'DISCORD_TOKEN=YOUR_TOKEN_HERE' > /home/botuser/discord-media-bot/.env
chmod 600 /home/botuser/discord-media-bot/.env
chown botuser:botuser /home/botuser/discord-media-bot/.env

# Start the bot
/home/botuser/manage_bots.sh start
/home/botuser/manage_bots.sh status
```

#### Option B: Manual Setup
```bash
# Update system
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git ffmpeg

# Create bot user
adduser botuser --disabled-password --gecos ""

# Clone and setup as botuser
su - botuser
git clone https://github.com/MalachiMindwyre/discord-media-bot.git
cd discord-media-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
exit

# Install screen (as root)
apt install -y screen

# Create management script
cat > /home/botuser/manage_bots.sh << 'EOF'
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
    ;;
esac
EOF

chmod +x /home/botuser/manage_bots.sh
chown botuser:botuser /home/botuser/manage_bots.sh

# Start the bot
/home/botuser/manage_bots.sh start
```

### Step 3: Transfer Configuration (Optional)
To preserve your existing bot settings from your local machine:
```bash
# From your local machine
scp bot_config.json root@YOUR_DROPLET_IP:/home/botuser/discord-media-bot/
ssh root@YOUR_DROPLET_IP "chown botuser:botuser /home/botuser/discord-media-bot/bot_config.json && /home/botuser/manage_bots.sh stop && /home/botuser/manage_bots.sh start"
```

## Management Commands

### Bot Control
```bash
/home/botuser/manage_bots.sh status  # Check status
/home/botuser/manage_bots.sh stop    # Stop bot
/home/botuser/manage_bots.sh start   # Start bot
```

### View Logs
```bash
# Attach to bot screen session
screen -r media_bot

# Detach from screen (bot keeps running)
# Press Ctrl+A then D

# List all screen sessions
screen -ls
```

### Update Bot
```bash
ssh root@YOUR_DROPLET_IP
su - botuser
cd discord-media-bot
git pull
source venv/bin/activate
pip install -r requirements.txt
exit
/home/botuser/manage_bots.sh stop
/home/botuser/manage_bots.sh start
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Bot not starting | Attach to screen: `screen -r media_bot` and check errors |
| Permission errors | Fix ownership: `chown -R botuser:botuser /home/botuser/discord-media-bot` |
| Bot offline | Verify Discord token in `.env` file |
| Can't connect via SSH | Ensure SSH key is added to droplet or use password auth |
| Screen session dead | Run `/home/botuser/manage_bots.sh start` to restart |

## Security

- **Firewall**: Enabled by default (SSH only)
- **Token Security**: Store in `.env` with 600 permissions
- **Updates**: Run `apt update && apt upgrade` regularly
- **Monitoring**: Use `htop` to monitor resources

## Costs

- **Droplet**: $6/month (1GB RAM)
- **Bandwidth**: 1TB included
- **Backups**: +20% (optional)

Perfect for Discord bots with minimal resource usage!