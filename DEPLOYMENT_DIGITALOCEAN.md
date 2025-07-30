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
systemctl start discord-bot
systemctl status discord-bot
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

# Create systemd service (as root)
cat > /etc/systemd/system/discord-bot.service << 'EOF'
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
EOF

# Enable and start
systemctl daemon-reload
systemctl enable discord-bot
systemctl start discord-bot
```

### Step 3: Transfer Configuration (Optional)
To preserve your existing bot settings from your local machine:
```bash
# From your local machine
scp bot_config.json root@YOUR_DROPLET_IP:/home/botuser/discord-media-bot/
ssh root@YOUR_DROPLET_IP "chown botuser:botuser /home/botuser/discord-media-bot/bot_config.json && systemctl restart discord-bot"
```

## Management Commands

### Bot Control
```bash
systemctl status discord-bot   # Check status
systemctl restart discord-bot  # Restart bot
systemctl stop discord-bot     # Stop bot
systemctl start discord-bot    # Start bot
```

### View Logs
```bash
journalctl -u discord-bot -f   # Live logs
journalctl -u discord-bot -n 100  # Last 100 lines
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
systemctl restart discord-bot
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Bot not starting | Check logs: `journalctl -u discord-bot -n 100` |
| Permission errors | Fix ownership: `chown -R botuser:botuser /home/botuser/discord-media-bot` |
| Bot offline | Verify Discord token in `.env` file |
| Can't connect via SSH | Ensure SSH key is added to droplet or use password auth |

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