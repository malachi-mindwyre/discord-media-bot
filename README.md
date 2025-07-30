# Discord Media Bot

A Discord bot that automatically collects media (images, videos, GIFs) from monitored channels and reposts them to a designated media channel. Perfect for creating media galleries, highlights channels, or content collections.

## Features

- **Media Filtering**: Automatically detects and copies media content (images, videos, GIFs)
- **Channel Monitoring**: Monitor specific channels or all channels in your server
- **Slash Commands**: Full support for Discord's slash command interface
- **Embed Support**: Properly handles embedded media from URLs including Twitter/X posts
- **Duplicate Prevention**: Advanced tracking ensures each piece of media is only copied once
- **Smart Delays**: Waits for embeds to fully load before processing
- **Consistent Display**: Media always appears before source information
- **Customization**: Toggle author attribution and other settings

## Commands

| Command | Description |
|---------|-------------|
| `/setup [channel]` | Set the channel where media will be copied to |
| `/monitor add [channel]` | Add a channel to the monitoring list |
| `/monitor remove [channel]` | Remove a channel from monitoring |
| `/monitor all [true/false]` | Toggle monitoring of all channels |
| `/monitor list` | Show current monitoring configuration |
| `/toggle_author` | Toggle whether to include original author information |
| `/help` | Show available commands and information |

## Quick Start

### Prerequisites
- Python 3.8+
- Discord bot token ([create one here](https://discord.com/developers/applications))

### Installation

```bash
# Clone the repository
git clone https://github.com/MalachiMindwyre/discord-media-bot.git
cd discord-media-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "DISCORD_TOKEN=your_token_here" > .env

# Run the bot
python discord-media-bot.py
```

### Invite Bot to Server

1. Go to Discord Developer Portal → Your Application → OAuth2 → URL Generator
2. Select Scopes: `bot` and `applications.commands`
3. Select Permissions: Send Messages, Read Messages, Embed Links, Attach Files
4. Use the generated URL to invite your bot

Or use this template:
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_CLIENT_ID&permissions=2147485696&scope=bot%20applications.commands
```

## Hosting Options

### Local Development
```bash
# Run in background
nohup python3 discord-media-bot.py > bot.log 2>&1 &

# Check logs
tail -f bot.log

# Stop bot
pkill -f "discord-media-bot.py"
```

### 24/7 Hosting

#### DigitalOcean (Recommended)
See [DEPLOYMENT_DIGITALOCEAN.md](DEPLOYMENT_DIGITALOCEAN.md) for detailed instructions.

Quick deployment:
```bash
# On your DigitalOcean droplet
wget https://raw.githubusercontent.com/MalachiMindwyre/discord-media-bot/main/deploy_to_digitalocean.sh
chmod +x deploy_to_digitalocean.sh
./deploy_to_digitalocean.sh
```

#### Other Options
- **Railway**: GitHub integration, easy deploy
- **Heroku**: $5-7/month for always-on
- **VPS**: Linode, Vultr (~$5/month)
- **Raspberry Pi**: One-time cost for home hosting

## Configuration

The bot stores settings in `bot_config.json`:
```json
{
  "monitored_channels": {"guild_id": [channel_ids]},
  "media_channels": {"guild_id": channel_id},
  "monitor_all": {"guild_id": boolean},
  "include_author": {"guild_id": boolean}
}
```

## Bot Permissions

Required permissions:
- Read Messages/View Channels
- Send Messages
- Embed Links
- Attach Files
- Use Slash Commands

Permission integer: `2147485696`

## Usage

1. **Setup**: `/setup #media-channel`
2. **Monitor**: `/monitor add #source-channel`
3. **Done!** Media from source channels will be copied to your media channel

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Bot offline | Check Discord token in `.env` |
| No media copying | Verify bot permissions in channels |
| Duplicate posts | Ensure only one bot instance is running |
| Missing embeds | Bot waits 8s for Twitter/X, 3s for others |

## Dependencies

- `discord.py==2.3.2` - Discord API wrapper
- `python-dotenv==1.0.0` - Environment variables
- `aiohttp==3.9.1` - Async HTTP client
- `pillow==10.1.0` - Image processing
- `yt-dlp==2023.12.30` - Video/media extraction
- `pydub==0.25.1` - Audio processing

## Contributing

Contributions welcome! Please submit a Pull Request.

## License

MIT License - see LICENSE file for details.

## Author

Created by Malachi Mindwyre - 2025

---

For detailed deployment instructions, see [DEPLOYMENT_DIGITALOCEAN.md](DEPLOYMENT_DIGITALOCEAN.md)
