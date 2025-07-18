import discord
from discord import app_commands
from discord.ext import commands
import os
import random
import string
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="/", intents=intents)

token = os.getenv("DISCORD_TOKEN")
guild_id = int(os.getenv("GUILD_ID"))
allowed_channel_id = int(os.getenv("ALLOWED_CHANNEL_ID"))

SCHEDULE_ROLE_ID = int(os.getenv("SCHEDULE_ROLE_ID"))
ANNOUNCE_ROLE_ID = int(os.getenv("ANNOUNCE_ROLE_ID"))
INFRACT_ROLE_ID = int(os.getenv("INFRACT_ROLE_ID"))
PROMOTE_ROLE_ID = int(os.getenv("PROMOTE_ROLE_ID"))
LOG_ROLE_ID = int(os.getenv("LOG_ROLE_ID"))
SUPPORT_FORUM_ID = int(os.getenv("SUPPORT_FORUM_ID"))

BANNER_URL = "https://media.discordapp.net/attachments/1395760490982150194/1395769069541789736/Banner1.png"

bot.support_forum_id = SUPPORT_FORUM_ID

def generate_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_footer():
    unix_timestamp = int(datetime.utcnow().timestamp())
    return f"ID: {generate_id()} | <t:{unix_timestamp}:f>"

@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(id=guild_id))
    print(f"Logged in as {bot.user}")

# Command: flight_schedule
@bot.tree.command(name="flight_schedule", description="Schedule a Jet2 flight", guild=discord.Object(id=guild_id))
@app_commands.describe(host="Host", time="Time", flight_info="Flight info", aircraft_type="Aircraft", flight_code="Code")
async def flight_schedule(interaction: discord.Interaction, host: str, time: str, flight_info: str, aircraft_type: str, flight_code: str):
    if SCHEDULE_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("No permission.", ephemeral=True)

    start_time = datetime.utcnow() + timedelta(minutes=5)
    end_time = start_time + timedelta(hours=1)

    event = await interaction.guild.create_scheduled_event(
        name=f"Jet2 Flight - {flight_code}",
        description=f"**Host:** {host}\n**Aircraft:** {aircraft_type}\n**Flight:** {flight_info}\n**Code:** {flight_code}",
        start_time=start_time,
        end_time=end_time,
        entity_type=discord.EntityType.external,
        location="Jet2 Airport",
        privacy_level=discord.PrivacyLevel.guild_only
    )

    await interaction.response.send_message(f"Event created for **{flight_code}**. [View]({event.url})")

# Command: flight_announce
@bot.tree.command(name="flight_announce", description="Announce a flight", guild=discord.Object(id=guild_id))
@app_commands.describe(time="Time", flight_info="Flight", aircraft="Aircraft", airport_link="Link", flight_code="Code", channel_id="Channel")
async def flight_announce(interaction: discord.Interaction, time: str, flight_info: str, aircraft: str, airport_link: str, flight_code: str, channel_id: str):
    if ANNOUNCE_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("No permission.", ephemeral=True)

    channel = bot.get_channel(int(channel_id))
    if not channel:
        return await interaction.response.send_message("Invalid channel ID.", ephemeral=True)

    embed = discord.Embed(
        title=":airplane: FLIGHT ANNOUNCEMENT",
        description=f"Flight today at {time} using the {aircraft}. From {flight_info}.\n**{flight_code}**",
        color=discord.Color.red()
    )
    embed.set_image(url=BANNER_URL)
    embed.set_footer(text=get_footer())

    await channel.send("@everyone")
    await channel.send(embed=embed)
    await interaction.response.send_message("Flight announced.", ephemeral=True)

# Command: infract
@bot.tree.command(name="infract", description="Discipline a staff member", guild=discord.Object(id=guild_id))
@app_commands.describe(user="User", reason="Reason", type="Action type", demotion_role="Demotion role")
async def infract(interaction: discord.Interaction, user: discord.Member, reason: str, type: str, demotion_role: discord.Role = None):
    if interaction.channel.id != allowed_channel_id:
        return await interaction.response.send_message("Wrong channel.", ephemeral=True)
    if INFRACT_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("No permission.", ephemeral=True)

    embed = discord.Embed(
        title="Infraction Notice",
        description=f"**By:** {interaction.user.mention}\n**User:** {user.mention}\n**Type:** {type}\n**Reason:** {reason}",
        color=0x8b2828
    )
    embed.set_image(url=BANNER_URL)
    embed.set_footer(text=get_footer())

    await interaction.channel.send(user.mention)
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("Logged.", ephemeral=True)

# Command: promote
@bot.tree.command(name="promote", description="Promote a staff member", guild=discord.Object(id=guild_id))
@app_commands.describe(user="User", promotion_to="New role", reason="Reason")
async def promote(interaction: discord.Interaction, user: discord.Member, promotion_to: str, reason: str):
    if interaction.channel.id != allowed_channel_id:
        return await interaction.response.send_message("Wrong channel.", ephemeral=True)
    if PROMOTE_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("No permission.", ephemeral=True)

    embed = discord.Embed(
        title="Promotion Notice",
        description=f"**By:** {interaction.user.mention}\n**User:** {user.mention}\n**To:** {promotion_to}\n**Reason:** {reason}",
        color=0x8b2828
    )
    embed.set_image(url=BANNER_URL)
    embed.set_footer(text=get_footer())

    await interaction.channel.send(user.mention)
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("Logged.", ephemeral=True)

# Command: flight_log
@bot.tree.command(name="flight_log", description="Log a flight", guild=discord.Object(id=guild_id))
@app_commands.describe(user="User", evidence="Image", session_date="Date", flight_code="Code")
async def flight_log(interaction: discord.Interaction, user: discord.Member, evidence: discord.Attachment, session_date: str, flight_code: str):
    if interaction.channel.id != allowed_channel_id:
        return await interaction.response.send_message("Wrong channel.", ephemeral=True)
    if LOG_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("No permission.", ephemeral=True)

    if not evidence.content_type.startswith("image"):
        return await interaction.response.send_message("Upload a valid image.", ephemeral=True)

    embed = discord.Embed(
        title="Flight Log",
        description=f"**By:** {interaction.user.mention}\n**User:** {user.mention}\n**Code:** {flight_code}\n**Date:** {session_date}",
        color=0x8b2828
    )
    embed.set_image(url=evidence.url)
    embed.set_footer(text=get_footer())

    await interaction.channel.send(user.mention)
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("Flight logged.", ephemeral=True)

# Load ticket system cog
async def load_cogs():
    await bot.load_extension("ticket_cog")

bot.loop.create_task(load_cogs())

bot.run(token)
