from typing import Optional
from rich import print
from functools import cache

import json
import os
import string
import shutil
import asyncio
import aiohttp

from discord import Guild, Member # type: ignore


header = """[bold white]
██████╗ ██╗███████╗ ██████╗ ██████╗ ██████╗ ██████╗     ███████╗ ██████╗██████╗  █████╗ ██████╗ ███████╗██████╗ 
██╔══██╗██║██╔════╝██╔════╝██╔═══██╗██╔══██╗██╔══██╗    ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
██║  ██║██║███████╗██║     ██║   ██║██████╔╝██║  ██║    ███████╗██║     ██████╔╝███████║██████╔╝█████╗  ██████╔╝
██║  ██║██║╚════██║██║     ██║   ██║██╔══██╗██║  ██║    ╚════██║██║     ██╔══██╗██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗
██████╔╝██║███████║╚██████╗╚██████╔╝██║  ██║██████╔╝    ███████║╚██████╗██║  ██║██║  ██║██║     ███████╗██║  ██║
╚═════╝ ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═════╝     ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝
[/]"""
info = """[bold black]
🏴 Made by Sxvxge.
[bold yellow]🚀 Star the repo: https://github.com/Sxvxgee/Discord-Scraper
[bold green]✅ Follow me: https://github.com/Sxvxgee/
[/]"""

default_data = {
  "token": "",
  "guild_id": 0,
  "pfp_format": "png",
  "purge_old_data": True,
  "download_pfp": True,
  "channel_id": 0
}


@cache
def show_header():
  print(f"{header}{info}")

@cache
def check_config_file():
  """
  Creates a config file if it doesn't exist.
  If it does, validates the config to required config.
  """
  if not os.path.isfile("config.json"): # Create a config file with default values if it doesn't exist
    json.dump(default_data, open("config.json", "w"), indent=2)
    return

  # Validating the JSON file, adding keys if they don't exist in it
  with open("config.json", "r") as file:
    file_data = json.loads(file.read())
  
  required_data = {}

  #TODO: The complexity of this part is more than required; could be shortened possibly.
  for key, value in file_data.items():
    if key in default_data.keys():
      required_data[key] = value

  for default_key, default_value in default_data.items():
    if default_key not in required_data.keys():
      required_data[default_key] = default_value

  json.dump(required_data, open("config.json", "w"), indent=2)


class Logger():
  def __init__(self) -> None:
    ...

  def scraper(self, text: str) -> None:
    print(f"[bold white][Scraper] {text} [/]")

  def success(self, text: str) -> None:
    print(f"[bold green][Success] {text} [/]")

  def error(self, text: str) -> None:
    print(f"[bold red][Error] {text} [/]")

  def custom(self, text: str, header: Optional[str] = None, color: str = "white") -> None:
    print(f"[bold {color}][{header}] {text} [/]")

@cache
def get_account_settings():
  return json.load(open("config.json"))

def create_guild_directory(guild: Guild):
  """Create directory for guild data (removed @cache to allow purging)"""
  if get_account_settings()["purge_old_data"]:
    # Fixed: Use consistent directory name
    shutil.rmtree(f"DataScraped/{guild.name}", ignore_errors=True)
  os.makedirs(f"DataScraped/{guild.name}", exist_ok=True)


def clean_string(string_to_clean: str) -> str:
  """Clean string to remove non-printable characters"""
  # Also remove characters that could cause file system issues
  cleaned = "".join([char for char in string_to_clean if char in string.printable])
  # Remove characters that are problematic for file names
  cleaned = cleaned.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
  # Remove excessive whitespace
  cleaned = ' '.join(cleaned.split())
  return cleaned[:200]  # Limit length to avoid filesystem issues

async def create_member_file(member: Member):
  """Create a text file with member information"""
  if member.bot:
    return

  try:
    username = clean_string(member.display_name)
    
    # Try to get profile with timeout
    try:
      profile = await asyncio.wait_for(member.guild.fetch_member_profile(member.id), timeout=10.0)
      bio = clean_string(profile.bio) if profile.bio else "User doesn't have a bio."
    except asyncio.TimeoutError:
      bio = "Could not fetch bio (timeout)."
    except Exception:
      bio = "Could not fetch bio."
    
    # Ensure directory exists
    os.makedirs(f"DataScraped/{member.guild.name}", exist_ok=True)
    
    with open(f"DataScraped/{member.guild.name}/{member.id}.txt", "w+", encoding='utf-8') as file:
      file.write(f"Username: {username}\nAccount ID: {member.id}\nBio: {bio}\nDiscriminator: #{member.discriminator}\n\n\nScraped by Discord-Scraper: https://github.com/Sxvxgee/Discord-Scraper/ \nFollow Sxvxge: https://github.com/Sxvxgee/")
  except Exception as e:
    print(f"[bold red][Error] Failed to write the data of the account \"{member}\": {e} [/]")

async def download_pfp(member: Member):
  """Download member's profile picture with better error handling"""
  if member.bot or member.avatar is None:
    return
  
  try:
    data = get_account_settings()
    
    # Ensure directory exists
    os.makedirs(f"DataScraped/{member.guild.name}", exist_ok=True)
    
    # Add timeout to avatar download
    await asyncio.wait_for(
      member.avatar.save(f"DataScraped/{member.guild.name}/{member.id}.{data['pfp_format']}"),
      timeout=30.0
    )
    
    # Small delay to avoid rate limiting
    await asyncio.sleep(0.1)
    
  except asyncio.TimeoutError:
    print(f"[bold red][Error] Timeout downloading profile picture for \"{member}\" [/]")
  except Exception as e:
    print(f"[bold red][Error] Failed to save the profile picture of the account \"{member}\": {e} [/]")
