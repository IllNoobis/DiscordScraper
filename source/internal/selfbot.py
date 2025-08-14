import random
import asyncio
from typing import List

from rich.progress import track
from discord import Client, Guild, Member
from discord.errors import InvalidData, HTTPException
from internal.utils import get_account_settings, create_guild_directory, create_member_file, download_pfp, Logger

client = Client(chunk_guilds_at_startup=False)
logger = Logger()


async def scrape_with_retry(config, guild: Guild, max_retries: int = 3) -> List[Member]:
    """Scrape members with retry logic and better error handling"""
    logger.scraper("Starting member scraping...")
    
    for attempt in range(max_retries):
        try:
            # Use specific channel if provided, otherwise try different approaches
            if config["channel_id"] != 0:
                # Try to get the specific channel
                channel = guild.get_channel(config["channel_id"])
                if channel:
                    logger.scraper(f"Attempting to scrape from channel: {channel.name}")
                    members = await guild.fetch_members([channel])
                else:
                    logger.error(f"Channel with ID {config['channel_id']} not found")
                    return []
            else:
                # Try different scraping strategies
                if attempt == 0:
                    # First attempt: try with a random text channel
                    text_channels = [ch for ch in guild.channels if hasattr(ch, 'send')]
                    if text_channels:
                        selected_channel = random.choice(text_channels)
                        logger.scraper(f"Attempt {attempt + 1}: Scraping from random channel: {selected_channel.name}")
                        members = await guild.fetch_members([selected_channel])
                    else:
                        logger.error("No text channels found in guild")
                        return []
                elif attempt == 1:
                    # Second attempt: try without specifying channels
                    logger.scraper(f"Attempt {attempt + 1}: Scraping without specific channel")
                    members = await guild.fetch_members(limit=None)
                else:
                    # Third attempt: try with delay and smaller chunks
                    logger.scraper(f"Attempt {attempt + 1}: Scraping with delay and chunking")
                    members = await guild.fetch_members(limit=1000, delay=2.0)
            
            # Filter out bots
            members = [member for member in members if not member.bot]
            logger.success(f"Successfully fetched {len(members)} members")
            return members
            
        except InvalidData as e:
            logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10  # Exponential backoff
                logger.scraper(f"Waiting {wait_time} seconds before retry...")
                await asyncio.sleep(wait_time)
            else:
                logger.error("All retry attempts failed")
                return []
        except HTTPException as e:
            logger.error(f"HTTP error on attempt {attempt + 1}: {str(e)}")
            if e.status == 429:  # Rate limited
                retry_after = getattr(e, 'retry_after', 60)
                logger.scraper(f"Rate limited. Waiting {retry_after} seconds...")
                await asyncio.sleep(retry_after)
            elif attempt < max_retries - 1:
                await asyncio.sleep((attempt + 1) * 5)
            else:
                return []
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep((attempt + 1) * 5)
            else:
                return []
    
    return []


@client.event
async def on_ready():
    logger.scraper(f"Logged in as {client.user}")

    config = get_account_settings()
    guild_id = config["guild_id"]

    guild = client.get_guild(int(guild_id))
    
    if not guild:
        logger.error(f"Could not find guild with ID: {guild_id}")
        logger.error("Make sure your account is a member of this guild")
        return

    logger.scraper(f"Found guild: {guild.name} (Members: {guild.member_count})")
    
    # Check if guild is too large
    if guild.member_count and guild.member_count > 10000:
        logger.scraper(f"Warning: Large guild ({guild.member_count} members). This may take a while or fail.")

    members = await scrape_with_retry(config, guild)
    
    if not members:
        logger.error("Could not fetch any members. This could be due to:")
        logger.error("1. Guild privacy settings")
        logger.error("2. Your account lacks permissions")
        logger.error("3. Rate limiting by Discord")
        logger.error("4. Network connectivity issues")
        return

    create_guild_directory(guild)

    # Process members with rate limiting
    for i, member in enumerate(track(members, description="[bold white][Scraper] Scraping profiles...[/]", refresh_per_second=10)):
        try:
            await create_member_file(member)
            if config["download_pfp"]:
                await download_pfp(member)
            
            # Add small delay every 10 members to avoid rate limiting
            if (i + 1) % 10 == 0:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Failed to process member {member}: {str(e)}")
            continue

    logger.success(f"Finished scraping {len(members)} member profiles and data.\n")
    logger.scraper("Don't forget to star the repo and follow Sxvxgee on github!")
