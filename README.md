# Discord Media Bot

A Discord bot that automatically collects media (images, videos, GIFs) from monitored channels and reposts them to a designated media channel. Perfect for creating media galleries, highlights channels, or content collections.

## Features

- **Media Filtering**: Automatically detects and copies media content (images, videos, GIFs)
- **Channel Monitoring**: Monitor specific channels or all channels in your server
- **Slash Commands**: Full support for Discord's slash command interface
- **Embed Support**: Properly handles embedded media from URLs including Twitter/X posts
- **Duplicate Prevention**: Advanced tracking ensures each piece of media is only copied once
- **Smart Delays**: Waits for embeds to fully load before processing (especially for Twitter/X)
- **Consistent Display**: Media always appears before source information
- **No Reactions**: Bot does not add any emoji reactions to messages
- **Customization**: Toggle author attribution and other settings
- **Simple Setup**: Easy-to-use commands for configuration

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

## Requirements

- Python 3.8 or higher
- discord.py 2.0 or higher
- A Discord bot token

## Setup Instructions

1. **Clone the repository**:

   ```bash
   git clone https://github.com/yourusername/discord-media-bot.git
   cd discord-media-bot
   ```

2. **Create a virtual environment**:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your Discord bot**:
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application and add a bot
   - Enable necessary intents (Message Content, Server Members, etc.)
   - Copy your bot token

5. **Configure environment variables**:
   - Create a `.env` file in the project directory
   - Add your bot token: `DISCORD_TOKEN=your_token_here`

6. **Run the bot**:

   ```bash
   python discord-media-bot.py
   ```

7. **Invite to your server**:
   - Generate an invite link in the Discord Developer Portal
   - Make sure to include the necessary permissions (read messages, send messages, embed links, attach files)

## Bot Setup in Discord

1. Invite the bot to your server
2. Use `/setup #channel` to set your media channel
3. Use `/monitor add #channel` to start monitoring a channel
4. Media will automatically be copied to your designated media channel

**Note**: You only need to invite the bot once. Updates to the bot are automatically available without re-invitation, as long as the bot has the necessary permissions.

## Configuration

The bot stores its configuration in a `bot_config.json` file with the following structure:

```json
{
  "monitored_channels": {
    "guild_id": [channel_ids]
  },
  "media_channels": {
    "guild_id": channel_id
  },
  "monitor_all": {
    "guild_id": boolean
  },
  "include_author": {
    "guild_id": boolean
  }
}
```

## Permissions

The bot requires the following permissions:

- **Read Messages/View Channels** - To see messages in monitored channels
- **Send Messages** - To post copied media to the destination channel
- **Embed Links** - To create info embeds with source details
- **Attach Files** - To upload/copy media files
- **Use Slash Commands** - For setup and monitoring commands

### Setting Up Permissions

When inviting the bot to your server:

1. **Go to Discord Developer Portal** → Your Application → OAuth2 → URL Generator
2. **Select Scopes**: `bot` and `applications.commands`
3. **Select Bot Permissions** (listed above)
4. **Use the generated invite URL**

**Quick Permission Integer**: `2147485696`

**Invite URL Format**:
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_CLIENT_ID&permissions=2147485696&scope=bot%20applications.commands
```

Replace `YOUR_BOT_CLIENT_ID` with your bot's Client ID from the Developer Portal.

## Running the Bot

### Local Development

When you run the bot locally using `python discord-media-bot.py`, it runs on your machine. To keep it running in the background:

```bash
# Start in background
nohup python3 discord-media-bot.py > bot.log 2>&1 &

# Check if running
ps aux | grep discord-media-bot

# View logs
tail -f bot.log

# Stop the bot
pkill -f "discord-media-bot.py"
```

**Important:** The bot only runs while your computer is on and connected to the internet. It will stop if you:
- Shut down or restart your computer
- Log out of your user account
- Put your computer to sleep
- Lose internet connection

### Production Hosting

For 24/7 operation without keeping your computer running, consider these hosting options:

#### Free Options
- **[Railway](https://railway.app)** - Easy deployment with GitHub integration
- **[Fly.io](https://fly.io)** - Free tier available with good uptime
- **[Render](https://render.com)** - Auto-deploys from GitHub

#### Paid Options
- **[Heroku](https://heroku.com)** - $5-7/month for always-on dyno
- **VPS Providers** - DigitalOcean, Linode, Vultr (~$5/month)
- **[AWS EC2](https://aws.amazon.com/ec2/)** - Free tier for 12 months
- **Raspberry Pi** - One-time cost (~$35-80) for home hosting

#### Quick Deploy to Railway

1. Fork this repository
2. Sign up for [Railway](https://railway.app)
3. Create new project → Deploy from GitHub repo
4. Add environment variable: `DISCORD_TOKEN`
5. Deploy!

The bot will automatically restart if it crashes and run 24/7.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Recent Updates

- **Fixed duplicate posting issue**: Implemented advanced message tracking to ensure each piece of media is only copied once
- **Improved Twitter/X embed detection**: Added smart delay system that waits longer for Twitter/X embeds to fully load
- **Enhanced queue management**: Better handling of message processing to prevent race conditions
- **Consistent media ordering**: Media content now always appears before the source information for better visual consistency
- **Clean display**: No emoji reactions - bot only copies media with source information
- **Token regeneration fix**: Resolved reaction issues by regenerating bot token to ensure clean behavior

## Troubleshooting

- **Bot posts duplicates**: Make sure you're running only one instance of the bot. Kill all instances with `pkill -f "discord-media-bot.py"` and restart
- **Twitter/X embeds not detected**: The bot now waits 8 seconds for Twitter/X embeds to load (vs 3 seconds for other media)
- **Bot not responding**: Check that the bot has proper permissions in both source and destination channels
- **Seeing emoji reactions**: The MediaMover bot does NOT add any reactions. Check for other bots or server auto-react features
- **Bot still adding reactions**: Regenerate your bot token in Discord Developer Portal - old tokens may have cached reaction behavior

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Credits

Created by Malachi Mindwyre - 2025
