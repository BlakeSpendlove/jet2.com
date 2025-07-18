import os
import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.dm_messages = True
intents.guild_messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

SUPPORT_FORUM_ID = os.getenv("SUPPORT_FORUM_ID")
if SUPPORT_FORUM_ID is None:
    raise ValueError("SUPPORT_FORUM_ID environment variable is not set.")
bot.SUPPORT_FORUM_ID = int(SUPPORT_FORUM_ID)

TOKEN = os.getenv("TOKEN")
if TOKEN is None:
    raise ValueError("TOKEN environment variable is not set.")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

async def main():
    await bot.load_extension("main_cog")
    await bot.load_extension("ticket_cog")
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
