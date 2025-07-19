import discord
from discord import app_commands
from discord.ext import commands
import os
import random
import string
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

token = os.getenv("DISCORD_TOKEN")
guild_id = int(os.getenv("GUILD_ID"))

INFRACT_CHANNEL_ID = int(os.getenv("INFRACT_CHANNEL_ID"))
PROMOTE_CHANNEL_ID = int(os.getenv("PROMOTE_CHANNEL_ID"))
FLIGHT_LOG_CHANNEL_ID = int(os.getenv("FLIGHT_LOG_CHANNEL_ID"))

SCHEDULE_ROLE_ID = int(os.getenv("SCHEDULE_ROLE_ID"))
ANNOUNCE_ROLE_ID = int(os.getenv("ANNOUNCE_ROLE_ID"))
INFRACT_ROLE_ID = int(os.getenv("INFRACT_ROLE_ID"))
PROMOTE_ROLE_ID = int(os.getenv("PROMOTE_ROLE_ID"))
LOG_ROLE_ID = int(os.getenv("LOG_ROLE_ID"))
VIEWLOGS_ROLE_ID = int(os.getenv("VIEWLOGS_ROLE_ID"))

BANNER_URL = "https://media.discordapp.net/attachments/1395760490982150194/1395769069541789736/Banner1.png"

bot = commands.Bot(command_prefix="!", intents=intents)

flight_logs = []

def generate_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_footer():
    return f"ID: {generate_id()} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}. Syncing commands...")
    try:
        await bot.tree.clear_commands(guild=discord.Object(id=guild_id))
        await bot.tree.sync(guild=discord.Object(id=guild_id))
        print(f"Commands cleared and synced for guild {guild_id}")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    print("Bot is ready.")

# --- Flight Schedule ---
@bot.tree.command(name="flight_schedule", description="Schedule a Jet2 flight")
@app_commands.describe(
    host="Select the host of the flight (Discord user mention)",
    date="Date of the flight (DD/MM/YYYY, British format)",
    start_time="Start time of the flight (24-hour format, e.g. 15:00)",
    end_time="End time of the flight (24-hour format, e.g. 17:00)",
    aircraft="Aircraft used (e.g. B737-800)",
    flight_code="Flight code (e.g. LS8800)"
)
async def flight_schedule(
    interaction: discord.Interaction,
    host: discord.Member,
    date: str,
    start_time: str,
    end_time: str,
    aircraft: str,
    flight_code: str,
):
    # Permission check
    if SCHEDULE_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)

    # Validate date format
    try:
        day, month, year = map(int, date.split('/'))
        event_date = datetime(year, month, day, tzinfo=timezone.utc)
    except Exception:
        return await interaction.response.send_message("❌ Invalid date format. Use DD/MM/YYYY.", ephemeral=True)

    # Validate time formats
    try:
        sh, sm = map(int, start_time.split(':'))
        eh, em = map(int, end_time.split(':'))
    except Exception:
        return await interaction.response.send_message("❌ Invalid time format. Use HH:MM 24-hour.", ephemeral=True)

    start_dt = datetime(year, month, day, sh, sm, tzinfo=timezone.utc)
    end_dt = datetime(year, month, day, eh, em, tzinfo=timezone.utc)

    if end_dt <= start_dt:
        return await interaction.response.send_message("❌ End time must be after start time.", ephemeral=True)

    try:
        event = await interaction.guild.create_scheduled_event(
            name=f"Jet2 Flight - {flight_code}",
            description=(
                f"**Host:** {host.mention}\n"
                f"**Aircraft:** {aircraft}\n"
                f"**Flight Date:** {date}\n"
                f"**Start Time:** {start_time}\n"
                f"**End Time:** {end_time}\n"
                f"**Flight Code:** {flight_code}"
            ),
            start_time=start_dt,
            end_time=end_dt,
            entity_type=discord.EntityType.external,
            location="Jet2 Airport",
            privacy_level=discord.PrivacyLevel.guild_only,
        )
    except Exception as e:
        return await interaction.response.send_message(f"❌ Failed to create event: {e}", ephemeral=True)

    await interaction.response.send_message(f"✅ Flight event created for **{flight_code}**. [View Event]({event.url})")

# --- Flight Announce ---
@bot.tree.command(name="flight_announce", description="Announce a flight")
@app_commands.describe(
    flight_code="Flight code (e.g. LS8800)",
    aircraft="Aircraft used (e.g. B737-800)",
    gate="Gate (e.g. A3)",
    stand="Stand (e.g. 5)",
    destination="Destination (e.g. London)",
    message="Custom message to add (optional)"
)
async def flight_announce(
    interaction: discord.Interaction,
    flight_code: str,
    aircraft: str,
    gate: str,
    stand: str,
    destination: str,
    message: str = None,
):
    if ANNOUNCE_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)

    embed = discord.Embed(
        title=f"Flight Announcement: {flight_code}",
        description=(
            f"**Aircraft:** {aircraft}\n"
            f"**Gate:** {gate}\n"
            f"**Stand:** {stand}\n"
            f"**Destination:** {destination}\n"
            + (f"\n**Message:** {message}" if message else "")
        ),
        color=discord.Color.green(),
        timestamp=datetime.utcnow()
    )
    embed.set_thumbnail(url=BANNER_URL)
    embed.set_footer(text=get_footer())

    await interaction.response.send_message(embed=embed)

# --- Infract ---
@bot.tree.command(name="infract", description="Record an infraction")
@app_commands.describe(
    user="User to infract",
    reason="Reason for the infraction"
)
async def infract(
    interaction: discord.Interaction,
    user: discord.Member,
    reason: str,
):
    if INFRACT_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)

    channel = bot.get_channel(INFRACT_CHANNEL_ID)
    if channel is None:
        return await interaction.response.send_message("❌ Infraction log channel not found.", ephemeral=True)

    embed = discord.Embed(
        title=f"Infraction for {user.display_name}",
        description=f"**Reason:** {reason}",
        color=discord.Color.red(),
        timestamp=datetime.utcnow()
    )
    embed.set_thumbnail(url=BANNER_URL)
    embed.set_footer(text=get_footer())

    await channel.send(embed=embed)
    await interaction.response.send_message(f"✅ Infraction recorded for {user.mention}.")

# --- Promote ---
@bot.tree.command(name="promote", description="Promote a user")
@app_commands.describe(
    user="User to promote",
    new_rank="New rank of the user"
)
async def promote(
    interaction: discord.Interaction,
    user: discord.Member,
    new_rank: str,
):
    if PROMOTE_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)

    channel = bot.get_channel(PROMOTE_CHANNEL_ID)
    if channel is None:
        return await interaction.response.send_message("❌ Promotion log channel not found.", ephemeral=True)

    embed = discord.Embed(
        title=f"Promotion for {user.display_name}",
        description=f"Promoted to **{new_rank}**",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    embed.set_thumbnail(url=BANNER_URL)
    embed.set_footer(text=get_footer())

    await channel.send(embed=embed)
    await interaction.response.send_message(f"✅ {user.mention} promoted to {new_rank}.")

# --- Flight Log ---
@bot.tree.command(name="flight_log", description="Log a flight")
@app_commands.describe(
    host="Host of the flight (Discord user mention)",
    aircraft="Aircraft used (e.g. B737-800)",
    flight_code="Flight code (e.g. LS8800)",
    notes="Additional notes (optional)"
)
async def flight_log(
    interaction: discord.Interaction,
    host: discord.Member,
    aircraft: str,
    flight_code: str,
    notes: str = None,
):
    if LOG_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)

    channel = bot.get_channel(FLIGHT_LOG_CHANNEL_ID)
    if channel is None:
        return await interaction.response.send_message("❌ Flight log channel not found.", ephemeral=True)

    unique_id = generate_id()
    timestamp = datetime.utcnow()

    embed = discord.Embed(
        title=f"Flight Log - {flight_code}",
        description=(
            f"**Host:** {host.mention}\n"
            f"**Aircraft:** {aircraft}\n"
            + (f"**Notes:** {notes}" if notes else "")
        ),
        color=discord.Color.gold(),
        timestamp=timestamp
    )
    embed.set_thumbnail(url=BANNER_URL)
    embed.set_footer(text=f"ID: {unique_id} | {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

    await channel.send(embed=embed)
    flight_logs.append({
        "id": unique_id,
        "timestamp": timestamp,
        "host": host.id,
        "aircraft": aircraft,
        "flight_code": flight_code,
        "notes": notes,
    })
    await interaction.response.send_message(f"✅ Flight logged for {flight_code} with ID {unique_id}.")

# --- View Logs ---
@bot.tree.command(name="view_logs", description="View flight logs from past 7 days (Sun-Sat)")
@app_commands.describe(
    user="User to view logs for"
)
async def view_logs(
    interaction: discord.Interaction,
    user: discord.Member,
):
    if VIEWLOGS_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)

    # Filter logs from past 7 days (Sunday to Saturday)
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)

    user_logs = [log for log in flight_logs if log["host"] == user.id and log["timestamp"] >= seven_days_ago]

    if not user_logs:
        return await interaction.response.send_message(f"No flight logs found for {user.mention} in the past 7 days.", ephemeral=True)

    embed = discord.Embed(
        title=f"Flight Logs for {user.display_name} (Past 7 Days)",
        color=discord.Color.purple(),
        timestamp=now
    )
    embed.set_thumbnail(url=BANNER_URL)

    for log in user_logs:
        desc = f"Flight Code: {log['flight_code']}\nAircraft: {log['aircraft']}\n"
        if log.get("notes"):
            desc += f"Notes: {log['notes']}\n"
        desc += f"Timestamp: {log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\nID: {log['id']}"
        embed.add_field(name="Flight Log Entry", value=desc, inline=False)

    embed.set_footer(text=get_footer())

    await interaction.response.send_message(embed=embed)

# Optional manual clear commands command
@bot.command()
async def clear_commands(ctx):
    if ctx.author.guild_permissions.administrator:
        await bot.tree.clear_commands(guild=discord.Object(id=guild_id))
        await bot.tree.sync(guild=discord.Object(id=guild_id))
        await ctx.send("✅ Cleared all guild-specific slash commands.")
    else:
        await ctx.send("❌ You don't have permission to do this.")

bot.run(token)
