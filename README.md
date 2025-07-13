# Discord Media Bot

A Discord bot that automatically collects media (images, videos, GIFs) from monitored channels and reposts them to a designated media channel. Perfect for creating media galleries, highlights channels, or content collections.

## Features

- **Media Filtering**: Automatically detects and copies media content (images, videos, GIFs)
- **Channel Monitoring**: Monitor specific channels or all channels in your server
- **Slash Commands**: Full support for Discord's slash command interface
- **Embed Support**: Properly handles embedded media from URLs including Twitter/X posts
- **Duplicate Prevention**: Advanced tracking ensures each piece of media is only copied once
- **Smart Delays**: Waits for embeds to fully load before processing (especially for Twitter/X)
- **Visual Feedback**: Adds 📸 reaction to copied messages
- **Consistent Display**: Media always appears before source information
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

- Read Messages/View Channels
- Send Messages
- Embed Links
- Attach Files
- Use Slash Commands

## Hosting

For 24/7 operation, consider hosting on:

- [Heroku](https://heroku.com)
- [Railway](https://railway.app)
- [Replit](https://replit.com)
- A VPS or dedicated server

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Recent Updates

- **Fixed duplicate posting issue**: Implemented advanced message tracking to ensure each piece of media is only copied once
- **Improved Twitter/X embed detection**: Added smart delay system that waits longer for Twitter/X embeds to fully load
- **Enhanced queue management**: Better handling of message processing to prevent race conditions
- **Camera reaction**: Bot now adds a 📸 emoji reaction to all copied media messages
- **Consistent media ordering**: Media content now always appears before the source information for better visual consistency

## Troubleshooting

- **Bot posts duplicates**: Make sure you're running only one instance of the bot. Kill all instances with `pkill -f "discord-media-bot.py"` and restart
- **Twitter/X embeds not detected**: The bot now waits 8 seconds for Twitter/X embeds to load (vs 3 seconds for other media)
- **Bot not responding**: Check that the bot has proper permissions in both source and destination channels

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Credits

Created by Malachi Mindwyre - 2025
