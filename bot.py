import discord
from discord import app_commands
from discord.ext import commands
import os
import random
import string
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
token = os.getenv("DISCORD_TOKEN")
guild_id = int(os.getenv("GUILD_ID"))

OWNER_ID = int(os.getenv("OWNER_ID"))  # Your Discord user ID
SCHEDULE_ROLE_ID = int(os.getenv("SCHEDULE_ROLE_ID"))
ANNOUNCE_ROLE_ID = int(os.getenv("ANNOUNCE_ROLE_ID"))
INFRACT_ROLE_ID = int(os.getenv("INFRACT_ROLE_ID"))
PROMOTE_ROLE_ID = int(os.getenv("PROMOTE_ROLE_ID"))
LOG_ROLE_ID = int(os.getenv("LOG_ROLE_ID"))
VIEWLOG_ROLE_ID = int(os.getenv("VIEWLOG_ROLE_ID"))

INFRACT_CHANNEL_ID = int(os.getenv("INFRACT_CHANNEL_ID"))
PROMOTE_CHANNEL_ID = int(os.getenv("PROMOTE_CHANNEL_ID"))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))

BANNER_URL = "https://media.discordapp.net/attachments/1395760490982150194/1395769069541789736/Banner1.png?ex=687ba6be&is=687a553e&hm=a96e719147a26743f923afbe2337735c43a22a2a657e1b0cd2e53820b75b0ad0&=&format=webp&quality=lossless&width=843&height=24"

bot = commands.Bot(command_prefix="/", intents=intents)

# ========== STARTUP ==========
@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(id=guild_id))
    print(f"Logged in as {bot.user}")

# ========== HELPERS ==========
def generate_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_footer():
    return f"ID: {generate_id()} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

# ========== CLEAR COMMANDS ==========
@bot.command()
async def clear_commands(ctx):
    if ctx.author.id != OWNER_ID:
        return await ctx.send("You don't have permission to use this.")
    await bot.tree.clear_commands(guild=discord.Object(id=guild_id))
    await bot.tree.sync(guild=discord.Object(id=guild_id))
    await ctx.send("✅ Cleared all slash commands. Restart the bot to re-register.")

# ========== YOUR EXISTING COMMANDS ==========
# Include all the commands here like flight_schedule, flight_announce, infract, promote, etc.
# (Already in your previous full script.)

# ========== /VIEW_LOGS COMMAND ==========
@bot.tree.command(name="view_logs", description="View logs of a user's flight attendance", guild=discord.Object(id=guild_id))
@app_commands.describe(user="User to check logs for")
async def view_logs(interaction: discord.Interaction, user: discord.Member):
    if VIEWLOG_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)

    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if not log_channel:
        return await interaction.response.send_message("Log channel not found.", ephemeral=True)

    logs = []
    async for message in log_channel.history(limit=100):
        if message.embeds:
            embed = message.embeds[0]
            if user.mention in embed.description and embed.title == "Flight Log":
                code_line = [line for line in embed.description.split("\n") if "Flight Code" in line]
                date_line = [line for line in embed.description.split("\n") if "Session Date" in line]
                code = code_line[0].split("**")[-2] if code_line else "Unknown"
                date = date_line[0].split("**")[-2] if date_line else "Unknown"
                logs.append(f"- **{code}** - {date} at {message.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

    if not logs:
        return await interaction.response.send_message(f"No flight logs found for {user.display_name}.", ephemeral=True)

    embed = discord.Embed(
        title=f"Flight Logs for {user.display_name}",
        description="\n".join(logs),
        color=discord.Color.blue()
    )
    embed.set_footer(text=get_footer())
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ========== RUN BOT ==========
bot.run(token)
