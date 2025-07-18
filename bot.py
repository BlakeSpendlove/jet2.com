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
bot = commands.Bot(command_prefix="/", intents=intents)

token = os.getenv("DISCORD_TOKEN")
guild_id = int(os.getenv("GUILD_ID"))

SCHEDULE_ROLE_ID = int(os.getenv("SCHEDULE_ROLE_ID"))
ANNOUNCE_ROLE_ID = int(os.getenv("ANNOUNCE_ROLE_ID"))
INFRACT_ROLE_ID = int(os.getenv("INFRACT_ROLE_ID"))
PROMOTE_ROLE_ID = int(os.getenv("PROMOTE_ROLE_ID"))
LOG_ROLE_ID = int(os.getenv("LOG_ROLE_ID"))
VIEW_LOGS_ROLE_ID = int(os.getenv("VIEW_LOGS_ROLE_ID"))

INFRACT_CHANNEL_ID = int(os.getenv("INFRACT_CHANNEL_ID"))
PROMOTE_CHANNEL_ID = int(os.getenv("PROMOTE_CHANNEL_ID"))
FLIGHT_LOG_CHANNEL_ID = int(os.getenv("FLIGHT_LOG_CHANNEL_ID"))

BANNER_URL = "https://media.discordapp.net/attachments/1395760490982150194/1395769069541789736/Banner1.png"

flight_logs = []

def generate_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_footer():
    return f"ID: {generate_id()} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(id=guild_id))
    print(f"Logged in as {bot.user}")

@bot.tree.command(name="flight_schedule", description="Schedule a Jet2 flight", guild=discord.Object(id=guild_id))
@app_commands.describe(host="Host", time="Time", flight_info="Route", aircraft_type="Aircraft", flight_code="Code")
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

    await interaction.response.send_message(f"Flight event created: [View Event]({event.url})", ephemeral=False)

@bot.tree.command(name="flight_announce", description="Announce a flight", guild=discord.Object(id=guild_id))
@app_commands.describe(time="Time", flight_info="Route", aircraft="Aircraft", airport_link="Link", flight_code="Code", channel_id="Channel")
async def flight_announce(interaction: discord.Interaction, time: str, flight_info: str, aircraft: str, airport_link: str, flight_code: str, channel_id: str):
    if ANNOUNCE_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("No permission.", ephemeral=True)

    channel = bot.get_channel(int(channel_id))
    if not channel:
        return await interaction.response.send_message("Invalid channel ID.", ephemeral=True)

    embed = discord.Embed(
        title=":airplane: FLIGHT ANNOUNCEMENT",
        description=f"Flight today at {time}.\nRoute: {flight_info}\nAircraft: {aircraft}\nFlight Code: **{flight_code}**",
        color=discord.Color.red()
    )
    embed.set_image(url=BANNER_URL)
    embed.set_footer(text=get_footer())

    await channel.send("@everyone")
    await channel.send(embed=embed)
    await interaction.response.send_message("Announced.", ephemeral=True)

@bot.tree.command(name="infract", description="Discipline staff", guild=discord.Object(id=guild_id))
@app_commands.describe(user="Staff", reason="Reason", type="Action", demotion_role="(Optional) Role")
async def infract(interaction: discord.Interaction, user: discord.Member, reason: str, type: str, demotion_role: discord.Role = None):
    if interaction.channel.id != INFRACT_CHANNEL_ID:
        return await interaction.response.send_message("Wrong channel.", ephemeral=True)
    if INFRACT_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("No permission.", ephemeral=True)

    embed = discord.Embed(title="Infraction Notice", description=f"**By:** {interaction.user.mention}\n**User:** {user.mention}\n**Type:** {type}\n**Reason:** {reason}", color=0x8b2828)
    embed.set_image(url=BANNER_URL)
    embed.set_footer(text=get_footer())
    await interaction.channel.send(user.mention)
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("Logged.", ephemeral=True)

@bot.tree.command(name="promote", description="Promote staff", guild=discord.Object(id=guild_id))
@app_commands.describe(user="User", promotion_to="New Role", reason="Reason")
async def promote(interaction: discord.Interaction, user: discord.Member, promotion_to: str, reason: str):
    if interaction.channel.id != PROMOTE_CHANNEL_ID:
        return await interaction.response.send_message("Wrong channel.", ephemeral=True)
    if PROMOTE_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("No permission.", ephemeral=True)

    embed = discord.Embed(title="Promotion Notice", description=f"**By:** {interaction.user.mention}\n**User:** {user.mention}\n**Promotion To:** {promotion_to}\n**Reason:** {reason}", color=0x8b2828)
    embed.set_image(url=BANNER_URL)
    embed.set_footer(text=get_footer())
    await interaction.channel.send(user.mention)
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("Promotion logged.", ephemeral=True)

@bot.tree.command(name="flight_log", description="Log a flight", guild=discord.Object(id=guild_id))
@app_commands.describe(user="Host", evidence="Evidence", session_date="Date", flight_code="Code")
async def flight_log(interaction: discord.Interaction, user: discord.Member, evidence: discord.Attachment, session_date: str, flight_code: str):
    if interaction.channel.id != FLIGHT_LOG_CHANNEL_ID:
        return await interaction.response.send_message("Wrong channel.", ephemeral=True)
    if LOG_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("No permission.", ephemeral=True)
    if not evidence.content_type.startswith("image"):
        return await interaction.response.send_message("Please upload a valid image.", ephemeral=True)

    log_entry = {
        "user_id": user.id,
        "flight_code": flight_code,
        "date": session_date,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    flight_logs.append(log_entry)

    embed = discord.Embed(title="Flight Log", description=f"**By:** {interaction.user.mention}\n**User:** {user.mention}\n**Flight Code:** {flight_code}\n**Date:** {session_date}", color=0x8b2828)
    embed.set_image(url=evidence.url)
    embed.set_footer(text=get_footer())
    await interaction.channel.send(user.mention)
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("Log submitted.", ephemeral=True)

@bot.tree.command(name="view_logs", description="View a user’s flight logs", guild=discord.Object(id=guild_id))
@app_commands.describe(user="User to view logs for")
async def view_logs(interaction: discord.Interaction, user: discord.Member):
    if VIEW_LOGS_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("No permission to view logs.", ephemeral=True)

    logs = [log for log in flight_logs if log['user_id'] == user.id]
    if not logs:
        return await interaction.response.send_message(f"No logs found for {user.display_name}.", ephemeral=True)

    lines = [f"- **{log['flight_code']}** - {log['date']} at {log['timestamp']}" for log in logs]
    embed = discord.Embed(title=f"Flight Logs for {user.display_name}", description="\n".join(lines), color=discord.Color.blue())
    embed.set_footer(text=get_footer())
    await interaction.response.send_message(embed=embed)

bot.run(token)
