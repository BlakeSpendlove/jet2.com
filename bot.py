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

# Flag to clear commands only once per run
commands_cleared = False

@bot.event
async def on_ready():
    global commands_cleared
    if not commands_cleared:
        print("Clearing guild commands to avoid duplicates...")
        await bot.tree.clear_commands(guild=discord.Object(id=guild_id))
        await bot.tree.sync(guild=discord.Object(id=guild_id))
        commands_cleared = True
        print("Commands cleared and synced.")
    else:
        await bot.tree.sync(guild=discord.Object(id=guild_id))
    print(f"Logged in as {bot.user}")

def generate_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_footer():
    return f"ID: {generate_id()} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

@bot.tree.command(name="flight_schedule", description="Schedule a Jet2 flight")
@app_commands.describe(host="Host of the flight", time="Time of the flight", flight_info="Flight route", aircraft_type="Aircraft used", flight_code="Flight code")
async def flight_schedule(interaction: discord.Interaction, host: str, time: str, flight_info: str, aircraft_type: str, flight_code: str):
    if SCHEDULE_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("You do not have permission to use this.", ephemeral=True)

    start_time = datetime.now(timezone.utc) + timedelta(minutes=5)
    end_time = start_time + timedelta(hours=1)

    event = await interaction.guild.create_scheduled_event(
        name=f"Jet2 Flight - {flight_code}",
        description=f"**Host:** {host}\n**Aircraft:** {aircraft_type}\n**Flight Schedule:** {flight_info}\n**Flight Code:** {flight_code}",
        start_time=start_time,
        end_time=end_time,
        entity_type=discord.EntityType.external,
        location="Jet2 Airport",
        privacy_level=discord.PrivacyLevel.guild_only
    )

    await interaction.response.send_message(f"Flight event created for **{flight_code}**. [View Event]({event.url})")

@bot.tree.command(name="flight_announce", description="Announce a flight")
@app_commands.describe(time="Flight time", flight_info="Flight info", aircraft="Aircraft used", airport_link="Airport link", flight_code="Flight code", channel_id="Channel ID")
async def flight_announce(interaction: discord.Interaction, time: str, flight_info: str, aircraft: str, airport_link: str, flight_code: str, channel_id: str):
    if ANNOUNCE_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("You do not have permission to use this.", ephemeral=True)

    channel = bot.get_channel(int(channel_id))
    if not channel:
        return await interaction.response.send_message("Invalid channel ID.", ephemeral=True)

    embed = discord.Embed(
        title=":airplane: FLIGHT ANNOUNCEMENT",
        description=f"There is a flight today at {time}.\nAircraft: {aircraft}\nRoute: {flight_info}\nJoin us for **{flight_code}**!",
        color=discord.Color.red()
    )
    embed.set_image(url=BANNER_URL)
    embed.set_footer(text=get_footer())

    await channel.send("@everyone")
    await channel.send(embed=embed)
    await interaction.response.send_message("Flight announced.", ephemeral=True)

@bot.tree.command(name="infract", description="Discipline a staff member")
@app_commands.describe(user="User to discipline", reason="Reason", type="Type of action", demotion_role="Optional demotion role")
async def infract(interaction: discord.Interaction, user: discord.Member, reason: str, type: str, demotion_role: discord.Role = None):
    if interaction.channel.id != INFRACT_CHANNEL_ID:
        return await interaction.response.send_message("Use this command in the infraction channel only.", ephemeral=True)
    if INFRACT_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("Permission denied.", ephemeral=True)

    embed = discord.Embed(
        title="Infraction Notice",
        description=f"**Infracted By:** {interaction.user.mention}\n**User:** {user.mention}\n**Type:** {type}\n**Reason:** {reason}",
        color=0x8b2828
    )
    embed.set_image(url=BANNER_URL)
    embed.set_footer(text=get_footer())

    await interaction.channel.send(user.mention)
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("Infraction logged.", ephemeral=True)

@bot.tree.command(name="promote", description="Promote a staff member")
@app_commands.describe(user="User to promote", promotion_to="New title", reason="Reason for promotion")
async def promote(interaction: discord.Interaction, user: discord.Member, promotion_to: str, reason: str):
    if interaction.channel.id != PROMOTE_CHANNEL_ID:
        return await interaction.response.send_message("Use this command in the promotion channel only.", ephemeral=True)
    if PROMOTE_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("Permission denied.", ephemeral=True)

    embed = discord.Embed(
        title="Promotion Notice",
        description=f"**Promoted By:** {interaction.user.mention}\n**User:** {user.mention}\n**Promotion To:** {promotion_to}\n**Reason:** {reason}",
        color=0x8b2828
    )
    embed.set_image(url=BANNER_URL)
    embed.set_footer(text=get_footer())

    await interaction.channel.send(user.mention)
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("Promotion logged.", ephemeral=True)

@bot.tree.command(name="flight_log", description="Log a flight")
@app_commands.describe(user="Flight host", evidence="Image evidence", session_date="Date", flight_code="Flight code")
async def flight_log(interaction: discord.Interaction, user: discord.Member, evidence: discord.Attachment, session_date: str, flight_code: str):
    if interaction.channel.id != FLIGHT_LOG_CHANNEL_ID:
        return await interaction.response.send_message("Use this command in the flight log channel only.", ephemeral=True)
    if LOG_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("Permission denied.", ephemeral=True)

    if not evidence.content_type.startswith("image"):
        return await interaction.response.send_message("Please upload a valid image.", ephemeral=True)

    embed = discord.Embed(
        title="Flight Log",
        description=f"**Logged By:** {interaction.user.mention}\n**User:** {user.mention}\n**Flight Code:** {flight_code}\n**Session Date:** {session_date}",
        color=0x8b2828
    )
    embed.set_image(url=evidence.url)
    embed.set_footer(text=get_footer())

    await interaction.channel.send(user.mention)
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("Flight log submitted.", ephemeral=True)

    flight_logs.append({
        "user_id": user.id,
        "flight_code": flight_code,
        "date": session_date,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@bot.tree.command(name="view_logs", description="View a user's flight logs")
@app_commands.describe(user="User to check")
async def view_logs(interaction: discord.Interaction, user: discord.Member):
    if VIEWLOGS_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("Permission denied.", ephemeral=True)

    user_logs = [log for log in flight_logs if log["user_id"] == user.id]

    if not user_logs:
        return await interaction.response.send_message(f"No logs found for {user.mention}.", ephemeral=True)

    log_text = "\n".join([f"- **{log['flight_code']}** - {log['date']} at {log['timestamp']}" for log in user_logs])
    embed = discord.Embed(
        title=f"Flight Logs for {user.display_name}",
        description=log_text,
        color=discord.Color.blue()
    )
    embed.set_footer(text=get_footer())
    await interaction.response.send_message(embed=embed)

@bot.command()
async def clear_commands(ctx):
    if ctx.author.guild_permissions.administrator:
        await bot.tree.clear_commands(guild=discord.Object(id=guild_id))
        await bot.tree.sync(guild=discord.Object(id=guild_id))
        await ctx.send("✅ Cleared all guild-specific slash commands.")
    else:
        await ctx.send("❌ You don't have permission to do this.")

bot.run(token)
