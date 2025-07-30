import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import aiohttp
import asyncio
from typing import Optional, List, Dict, Any, Set
import logging
import io
import re
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration file path
CONFIG_FILE = "bot_config.json"

class MediaCopyBot(commands.Bot):
    def __init__(self):
        # Set up intents - required for discord.py v2.x
        intents = discord.Intents.default()
        intents.message_content = True  # Required for reading message content
        intents.guilds = True  # Required for guild operations
        
        super().__init__(
            command_prefix="!",  # Keep prefix for backup, but primarily use slash commands
            intents=intents,
            help_command=None
        )
        
        # Load configuration
        self.config = self.load_config()
        
        # Add event for when the bot is ready to sync commands
        self.setup_hook_ran = False
        
        # Keep track of recently processed message IDs to prevent multi-posting
        # Using a dict to store both the message ID and the timestamp
        self.recently_processed = {}
        
        # Track message IDs that have been successfully copied
        self.copied_messages = set()
        
        # Message processing queue - stores all messages for batch processing
        self.message_queue = []
        self.queue_lock = asyncio.Lock()  # Lock for thread-safe queue operations
        
        # Batch processing settings
        self.batch_delay = 5  # seconds between batch processing
        self.processing_batch = False
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    
                # Migration: Add excluded_channels if missing
                if "excluded_channels" not in config:
                    config["excluded_channels"] = {}
                    logger.info("Added excluded_channels to existing config")
                    self.save_config(config)
                    
                return config
            except json.JSONDecodeError:
                logger.error("Invalid JSON in config file, creating new config")
        
        # Default configuration
        default_config = {
            "monitored_channels": {},  # guild_id: [channel_ids]
            "media_channels": {},      # guild_id: channel_id
            "include_author": {},      # guild_id: boolean
            "monitor_all": {},         # guild_id: boolean
            "excluded_channels": {}    # guild_id: [channel_ids] - excluded when monitor_all is True
        }
        
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config: Dict[str, Any] = None):
        """Save configuration to JSON file"""
        if config is None:
            config = self.config
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    
    async def setup_hook(self):
        """Called when the bot is first setting up before login"""
        if not self.setup_hook_ran:  # Prevent running twice
            logger.info("Syncing commands with Discord...")
            # This sync can take time, so it's important to only do it once during startup
            try:
                # Global sync to make commands available in all guilds
                await self.tree.sync()
                logger.info("Commands synced globally!")
                
                # Also sync to each guild for immediate updates
                for guild in self.guilds:
                    await self.tree.sync(guild=discord.Object(id=guild.id))
                    logger.info(f"Commands synced to guild: {guild.name}")
            except Exception as e:
                logger.error(f"Error syncing commands: {e}")
                
            self.setup_hook_ran = True
            
            # Start the batch processing task
            self.loop.create_task(self._batch_processor())
        
    async def on_ready(self):
        """Event handler for when the bot is ready"""
        logger.info(f"{self.user} has connected to Discord!")
        logger.info(f"Bot is in {len(self.guilds)} guilds")
        
        # Initialize config for all guilds
        for guild in self.guilds:
            guild_id = str(guild.id)
            if guild_id not in self.config["monitored_channels"]:
                self.config["monitored_channels"][guild_id] = []
            if guild_id not in self.config["media_channels"]:
                self.config["media_channels"][guild_id] = None
            if guild_id not in self.config["include_author"]:
                self.config["include_author"][guild_id] = True
            if guild_id not in self.config["monitor_all"]:
                self.config["monitor_all"][guild_id] = False
            if guild_id not in self.config["excluded_channels"]:
                self.config["excluded_channels"][guild_id] = []
        
        self.save_config()
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="for media content"
            )
        )
    
    async def on_message(self, message):
        """Handle incoming messages"""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Prevent multi-processing the same message
        if message.id in self.recently_processed:
            return
        
        # Add to tracking collections with current timestamp
        current_time = datetime.now()
        self.recently_processed[message.id] = current_time
        
        # Process commands first and immediately
        ctx = await self.get_context(message)
        if ctx.valid:  # If this is a valid command, only process it as a command
            try:
                await self.process_commands(message)
            except Exception as e:
                logger.error(f"Error processing command: {e}")
            return
        
        # For non-command messages, add to the processing queue
        # Only add if not already copied
        if message.id not in self.copied_messages:
            async with self.queue_lock:
                # Check if message is already in queue
                existing = any(item['message'].id == message.id for item in self.message_queue)
                if not existing:
                    self.message_queue.append({
                        'message': message,
                        'time': current_time,
                        'processed': False
                    })
                    logger.debug(f"Added message {message.id} to queue. Queue size: {len(self.message_queue)}")
    
    def _contains_twitter_link(self, message) -> bool:
        """Check if message contains Twitter/X links"""
        # Match twitter.com, x.com, and their variants
        twitter_pattern = re.compile(r'https?://(?:www\.)?(twitter\.com|x\.com)', re.IGNORECASE)
        return bool(message.content and twitter_pattern.search(message.content))
    
    def _cleanup_message_tracking(self, current_time):
        """Clean up message tracking collections"""
        # Keep messages processed in the last 5 minutes
        cutoff_time = current_time - timedelta(minutes=5)
        
        # Clean up recently_processed dict
        self.recently_processed = {msg_id: timestamp for msg_id, timestamp in self.recently_processed.items() 
                               if timestamp > cutoff_time}
        
        # Limit the size of copied_messages
        if len(self.copied_messages) > 500:
            # Convert to list, keep most recent 300 items
            self.copied_messages = set(list(self.copied_messages)[-300:])
    
    async def _batch_processor(self):
        """Periodically process messages in batches"""
        await self.wait_until_ready()
        while not self.is_closed():
            try:
                # Wait for the specified batch delay
                await asyncio.sleep(self.batch_delay)
                
                # Set processing flag
                self.processing_batch = True
                
                # Process messages in the queue
                await self._process_queued_messages()
                
                # Reset processing flag
                self.processing_batch = False
                
            except Exception as e:
                logger.error(f"Error in batch processor: {e}")
    
    async def _process_queued_messages(self):
        """Process all messages in the queue"""
        # Skip if queue is empty
        if not self.message_queue:
            return
            
        # Get current time for cleanup
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(minutes=5)
        
        # Create a copy of the queue to process
        async with self.queue_lock:
            processing_queue = []
            for item in self.message_queue:
                if item['processed']:
                    continue
                    
                # Calculate wait time based on message content
                message = item['message']
                wait_seconds = 3  # Default wait time
                
                # Check if message contains Twitter/X links - they need more time for embeds
                if self._contains_twitter_link(message):
                    wait_seconds = 8  # Twitter embeds take longer to load
                
                # Check if enough time has passed
                if (current_time - item['time']).total_seconds() >= wait_seconds:
                    processing_queue.append(item)
                    item['processing'] = True
        
        # Process each message
        processed_count = 0
        for item in processing_queue:
            try:
                # Get the message
                message = item['message']
                
                # Skip if already copied
                if message.id in self.copied_messages:
                    item['processed'] = True
                    continue
                
                # Try to get a fresh copy of the message with potentially loaded embeds
                try:
                    channel = self.get_channel(message.channel.id)
                    if channel:
                        message = await channel.fetch_message(message.id)
                except Exception as e:
                    # If we can't fetch the message, use the original one
                    logger.debug(f"Could not fetch fresh message: {e}")
                
                # Check if it should be copied and copy it
                if await self.should_copy_message(message):
                    await self.copy_media_message(message)
                    processed_count += 1
                
                # Mark as processed
                item['processed'] = True
                
            except Exception as e:
                logger.error(f"Error processing message in batch: {e}")
        
        # Clean up the queue - remove processed and old messages
        async with self.queue_lock:
            self.message_queue = [
                item for item in self.message_queue 
                if not item['processed'] and item['time'] > cutoff_time
            ]
            
        # Clean up tracking
        self._cleanup_message_tracking(current_time)
            
        if processed_count > 0:
            logger.info(f"Batch processed {processed_count} messages. Queue size now: {len(self.message_queue)}")
    
    async def should_copy_message(self, message) -> bool:
        """Check if message contains media and is from a monitored channel"""
        if not message.guild:
            return False
            
        guild_id = str(message.guild.id)
        
        # Check if guild is configured
        if guild_id not in self.config["monitored_channels"]:
            return False
            
        # Check if media channel is set
        media_channel_id = self.config["media_channels"].get(guild_id)
        if not media_channel_id:
            return False
            
        # Don't copy from the media channel itself
        if message.channel.id == media_channel_id:
            return False
            
        # Check monitoring mode
        if self.config["monitor_all"].get(guild_id, False):
            # Monitor all channels except media channel and excluded channels
            excluded_channels = self.config["excluded_channels"].get(guild_id, [])
            if message.channel.id in excluded_channels:
                return False
        else:
            # Check if channel is in monitored list
            if message.channel.id not in self.config["monitored_channels"][guild_id]:
                return False
            
        # Check if message has media content
        return self.has_media_content(message)
    
    def has_media_content(self, message) -> bool:
        """
        Check if message contains embedded media or attachments
        This includes:
        - Directly uploaded files (images, videos, GIFs)
        - Embedded media from URLs (when Discord shows a preview)
        - Twitter/X links with media content
        """
        # Check for direct uploads (attachments)
        if message.attachments:
            for attachment in message.attachments:
                # Check if attachment is image/video/gif
                if any(attachment.filename.lower().endswith(ext) for ext in 
                       ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.mp4', 
                        '.mov', '.avi', '.webm', '.bmp', '.tiff']):
                    return True
        
        # Check for embedded media (from URLs)
        if message.embeds:
            for embed in message.embeds:
                # Check for image/video content or rich embeds with media
                if embed.image or embed.video:
                    return True
                if embed.thumbnail:
                    # Only count thumbnails from certain embed types
                    if embed.type in ['image', 'video', 'gifv', 'article', 'link', 'rich']:
                        return True
                # Check by embed type
                if embed.type in ['image', 'video', 'gifv']:
                    return True
                # Special handling for Twitter/X embeds
                if embed.type in ['link', 'rich', 'article']:
                    # Check if it's a Twitter/X link with media
                    if (embed.url and ('twitter.com' in embed.url or 'x.com' in embed.url)) and \
                       (embed.thumbnail or embed.image or embed.video):
                        return True
        
        return False
    
    async def copy_media_message(self, message):
        """Copy message with media to the designated media channel"""
        try:
            # Mark as copied immediately to prevent duplicates
            self.copied_messages.add(message.id)
            
            guild_id = str(message.guild.id)
            media_channel_id = self.config["media_channels"][guild_id]
            media_channel = self.get_channel(media_channel_id)
            
            if not media_channel:
                logger.warning(f"Media channel {media_channel_id} not found")
                return
            
            # Check bot permissions in media channel
            permissions = media_channel.permissions_for(message.guild.me)
            if not permissions.send_messages or not permissions.attach_files:
                logger.warning(f"Missing permissions in {media_channel.name}")
                return
            
            # Rate limit check - avoid spamming
            await asyncio.sleep(0.5)
            
            # Create new embed for the copied message
            include_author = self.config["include_author"][guild_id]
            
            # Handle direct file uploads
            files = []
            if message.attachments:
                for attachment in message.attachments:
                    # Check file size (Discord bot limit is 8MB)
                    if attachment.size <= 8 * 1024 * 1024:
                        try:
                            # Download attachment
                            async with aiohttp.ClientSession() as session:
                                async with session.get(attachment.url) as resp:
                                    if resp.status == 200:
                                        file_data = await resp.read()
                                        files.append(
                                            discord.File(
                                                io.BytesIO(file_data),
                                                filename=attachment.filename,
                                                spoiler=attachment.is_spoiler()
                                            )
                                        )
                        except Exception as e:
                            logger.error(f"Error downloading attachment: {e}")
            
            # Create info embed
            embed = discord.Embed(
                description=message.content[:1024] if message.content else None,
                color=0x00ff00,
                timestamp=message.created_at
            )
            
            if include_author:
                embed.set_author(
                    name=f"{message.author.display_name}",
                    icon_url=message.author.display_avatar.url
                )
            
            embed.add_field(
                name="Source",
                value=f"#{message.channel.name}",
                inline=True
            )
            
            embed.add_field(
                name="Jump to Original",
                value=f"[Click here]({message.jump_url})",
                inline=True
            )
            
            # Prepare embeds to send - media first, then info
            embeds_to_send = []
            
            # Copy original embeds first (for URL embeds with media)
            if message.embeds:
                for original_embed in message.embeds[:9]:  # Max 10 embeds total
                    try:
                        # Only copy embeds that have media
                        if (original_embed.image or original_embed.video or 
                            original_embed.thumbnail or original_embed.type in ['image', 'video', 'gifv']):
                            new_embed = discord.Embed.from_dict(original_embed.to_dict())
                            embeds_to_send.append(new_embed)
                    except Exception as e:
                        logger.warning(f"Could not copy embed: {e}")
            
            # Add info embed last so it appears after media
            embeds_to_send.append(embed)
            
            # Send the copied message
            await media_channel.send(
                files=files,
                embeds=embeds_to_send
            )
            
            logger.info(f"Copied media from #{message.channel.name} to #{media_channel.name}")
            
        except discord.HTTPException as e:
            logger.error(f"Discord API error: {e}")
        except Exception as e:
            logger.error(f"Error copying message: {e}")

# Initialize bot
bot = MediaCopyBot()

# Disable command processing through the default on_message event
bot._skip_check = lambda x, y: False

# Command: Set up media channel
@bot.hybrid_command(name="setup", description="Set the media channel for this server")
@commands.has_permissions(manage_channels=True)
async def setup_media_channel(ctx, channel: discord.TextChannel):
    """Set up the media channel for this server"""
    guild_id = str(ctx.guild.id)
    bot.config["media_channels"][guild_id] = channel.id
    bot.save_config()
    
    embed = discord.Embed(
        title="✅ Media Channel Set",
        description=f"Media will be copied to {channel.mention}",
        color=0x00ff00
    )
    await ctx.send(embed=embed)

# Command group: Monitor
@bot.hybrid_group(name="monitor", description="Manage channel monitoring")
@commands.has_permissions(manage_channels=True)
async def monitor_group(ctx):
    """Parent group for monitoring commands"""
    if ctx.invoked_subcommand is None:
        await ctx.send("Use `/monitor help` for available commands")

@monitor_group.command(name="add", description="Add a channel to monitor")
async def monitor_add(ctx, channel: discord.TextChannel):
    """Add a channel to monitor for media"""
    guild_id = str(ctx.guild.id)
    
    if guild_id not in bot.config["monitored_channels"]:
        bot.config["monitored_channels"][guild_id] = []
    
    if channel.id not in bot.config["monitored_channels"][guild_id]:
        bot.config["monitored_channels"][guild_id].append(channel.id)
        bot.save_config()
        
        embed = discord.Embed(
            title="✅ Channel Added",
            description=f"Now monitoring {channel.mention} for media",
            color=0x00ff00
        )
    else:
        embed = discord.Embed(
            title="ℹ️ Already Monitoring",
            description=f"Already monitoring {channel.mention}",
            color=0xffff00
        )
    
    await ctx.send(embed=embed)

@monitor_group.command(name="remove", description="Remove a channel from monitoring")
async def monitor_remove(ctx, channel: discord.TextChannel):
    """Remove a channel from monitoring"""
    guild_id = str(ctx.guild.id)
    
    if (guild_id in bot.config["monitored_channels"] and 
        channel.id in bot.config["monitored_channels"][guild_id]):
        
        bot.config["monitored_channels"][guild_id].remove(channel.id)
        bot.save_config()
        
        embed = discord.Embed(
            title="✅ Channel Removed",
            description=f"No longer monitoring {channel.mention}",
            color=0x00ff00
        )
    else:
        embed = discord.Embed(
            title="ℹ️ Not Monitoring",
            description=f"Was not monitoring {channel.mention}",
            color=0xffff00
        )
    
    await ctx.send(embed=embed)

@monitor_group.command(name="exclude", description="Exclude a channel from monitoring when monitor_all is enabled")
async def monitor_exclude(ctx, channel: discord.TextChannel):
    """Exclude a channel from monitoring when monitor_all is enabled"""
    guild_id = str(ctx.guild.id)
    
    if guild_id not in bot.config["excluded_channels"]:
        bot.config["excluded_channels"][guild_id] = []
    
    if channel.id not in bot.config["excluded_channels"][guild_id]:
        bot.config["excluded_channels"][guild_id].append(channel.id)
        bot.save_config()
        
        embed = discord.Embed(
            title="✅ Channel Excluded",
            description=f"Excluded {channel.mention} from monitoring (when monitor_all is enabled)",
            color=0x00ff00
        )
    else:
        embed = discord.Embed(
            title="ℹ️ Already Excluded",
            description=f"Already excluding {channel.mention}",
            color=0xffff00
        )
    
    await ctx.send(embed=embed)

@monitor_group.command(name="include", description="Remove a channel from the exclusion list")
async def monitor_include(ctx, channel: discord.TextChannel):
    """Remove a channel from the exclusion list"""
    guild_id = str(ctx.guild.id)
    
    if (guild_id in bot.config["excluded_channels"] and 
        channel.id in bot.config["excluded_channels"][guild_id]):
        
        bot.config["excluded_channels"][guild_id].remove(channel.id)
        bot.save_config()
        
        embed = discord.Embed(
            title="✅ Channel Included",
            description=f"Removed {channel.mention} from exclusion list",
            color=0x00ff00
        )
    else:
        embed = discord.Embed(
            title="ℹ️ Not Excluded",
            description=f"Was not excluding {channel.mention}",
            color=0xffff00
        )
    
    await ctx.send(embed=embed)

@monitor_group.command(name="all", description="Toggle monitoring all channels")
async def monitor_all(ctx, enabled: bool = None):
    """Toggle monitoring all channels except media channel"""
    guild_id = str(ctx.guild.id)
    
    if enabled is None:
        current = bot.config["monitor_all"].get(guild_id, False)
        enabled = not current
    
    bot.config["monitor_all"][guild_id] = enabled
    bot.save_config()
    
    if enabled:
        bot.config["monitored_channels"][guild_id] = []
        bot.save_config()
        excluded_count = len(bot.config["excluded_channels"].get(guild_id, []))
        if excluded_count > 0:
            status = f"🌐 Now monitoring **all channels** (except destination + {excluded_count} excluded)"
        else:
            status = "🌐 Now monitoring **all channels** (except destination)"
    else:
        status = "📍 Switched to monitoring **specific channels only**"
    
    embed = discord.Embed(
        title="✅ Monitor Mode Updated",
        description=status,
        color=0x00ff00
    )
    await ctx.send(embed=embed)

@monitor_group.command(name="list", description="List all monitored channels")
async def monitor_list(ctx):
    """Show current monitoring configuration"""
    guild_id = str(ctx.guild.id)
    
    embed = discord.Embed(
        title="📺 Media Monitoring Status",
        color=0x0099ff
    )
    
    # Media channel
    media_channel_id = bot.config["media_channels"].get(guild_id)
    if media_channel_id:
        media_channel = bot.get_channel(media_channel_id)
        embed.add_field(
            name="📸 Media Channel",
            value=media_channel.mention if media_channel else "Channel not found",
            inline=False
        )
    else:
        embed.add_field(
            name="📸 Media Channel",
            value="Not configured (use `/setup`)",
            inline=False
        )
    
    # Monitor mode
    if bot.config["monitor_all"].get(guild_id, False):
        embed.add_field(
            name="🌐 Monitor Mode",
            value="All channels (except destination)",
            inline=False
        )
    else:
        # Monitored channels
        monitored = bot.config["monitored_channels"].get(guild_id, [])
        if monitored:
            channels = []
            for channel_id in monitored:
                channel = bot.get_channel(channel_id)
                if channel:
                    channels.append(channel.mention)
            
            embed.add_field(
                name="📍 Monitored Channels",
                value="\n".join(channels) if channels else "No valid channels",
                inline=False
            )
        else:
            embed.add_field(
                name="📍 Monitored Channels",
                value="None (use `/monitor add`)",
                inline=False
            )
    
    # Author attribution
    include_author = bot.config["include_author"].get(guild_id, True)
    embed.add_field(
        name="👤 Author Attribution",
        value="Enabled" if include_author else "Disabled",
        inline=True
    )
    
    await ctx.send(embed=embed)

@bot.hybrid_command(name="toggle_author", description="Toggle author attribution")
@commands.has_permissions(manage_channels=True)
async def toggle_author_attribution(ctx):
    """Toggle author attribution in copied messages"""
    guild_id = str(ctx.guild.id)
    
    current = bot.config["include_author"].get(guild_id, True)
    bot.config["include_author"][guild_id] = not current
    bot.save_config()
    
    status = "enabled" if not current else "disabled"
    embed = discord.Embed(
        title="✅ Author Attribution Updated",
        description=f"Author attribution is now **{status}**",
        color=0x00ff00
    )
    await ctx.send(embed=embed)

@bot.hybrid_command(name="help", description="Show available commands and information")
async def help_command(ctx):
    """Show help information"""
    embed = discord.Embed(
        title="📸 Media Copy Bot Help",
        description="This bot copies media content (images, videos, GIFs) to a designated channel.",
        color=0x0099ff
    )
    
    embed.add_field(
        name="Setup Commands",
        value=(
            "`/setup #channel` - Set the media destination channel\n"
            "`/monitor add #channel` - Add a channel to monitor\n"
            "`/monitor remove #channel` - Stop monitoring a channel\n"
            "`/monitor all` - Toggle monitoring all channels\n"
            "`/monitor exclude #channel` - Exclude channel from monitor_all\n"
            "`/monitor include #channel` - Remove channel from exclusions\n"
            "`/monitor list` - Show current configuration"
        ),
        inline=False
    )
    
    embed.add_field(
        name="Other Commands",
        value=(
            "`/toggle_author` - Toggle showing who posted the media\n"
            "`/help` - Show this help message"
        ),
        inline=False
    )
    
    embed.add_field(
        name="What gets copied?",
        value=(
            "• Directly uploaded images/videos/GIFs\n"
            "• Embedded media from URLs (previews)\n"
            "• Does NOT copy plain text links"
        ),
        inline=False
    )
    
    embed.set_footer(text="All commands require 'Manage Channels' permission")
    
    await ctx.send(embed=embed)

# Error handling
@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="❌ Permission Error",
            description="You need 'Manage Channels' permission to use this command",
            color=0xff0000
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.ChannelNotFound):
        embed = discord.Embed(
            title="❌ Channel Not Found",
            description="Please mention a valid channel",
            color=0xff0000
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.CommandNotFound):
        # Ignore command not found errors
        pass
    else:
        logger.error(f"Unhandled error: {error}")

if __name__ == "__main__":
    # Get token from environment variable
    TOKEN = os.getenv("DISCORD_TOKEN")
    
    if not TOKEN:
        print("❌ Please set DISCORD_TOKEN environment variable")
        print("Create a .env file with: DISCORD_TOKEN=your_bot_token_here")
        exit(1)
    
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("❌ Invalid bot token! Please check your DISCORD_TOKEN")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")