import discord
from discord.ext import commands
from discord import app_commands
import os
import random
import string
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
SCHEDULE_ROLE_ID = int(os.getenv("SCHEDULE_ROLE_ID"))
ANNOUNCE_ROLE_ID = int(os.getenv("ANNOUNCE_ROLE_ID"))
INFRACT_ROLE_ID = int(os.getenv("INFRACT_ROLE_ID"))
PROMOTE_ROLE_ID = int(os.getenv("PROMOTE_ROLE_ID"))
LOG_ROLE_ID = int(os.getenv("LOG_ROLE_ID"))
ALLOWED_CHANNEL_ID = int(os.getenv("ALLOWED_CHANNEL_ID"))

BANNER_URL = "https://media.discordapp.net/attachments/1395760490982150194/1395769069541789736/Banner1.png"

intents = discord.Intents.default()
intents.message_content = True
tree = app_commands.CommandTree(commands.Bot(command_prefix="!", intents=intents))
bot = commands.Bot(command_prefix="!", intents=intents)

def generate_footer():
    unique_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"ID: {unique_id} | {timestamp}"

@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"Bot is online as {bot.user}")

@tree.command(name="flight_schedule", description="Schedule a Jet2 flight", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    host="Host of the flight (mention)",
    time="Flight time (e.g. 18:00 GMT)",
    flight_info="Flight route (e.g. Bournemouth -> Punta Cana)",
    aircraft_type="Aircraft used (e.g. B737-800)",
    flight_code="Flight code (e.g. LS8800)"
)
async def flight_schedule(interaction: discord.Interaction, host: str, time: str, flight_info: str, aircraft_type: str, flight_code: str):
    if SCHEDULE_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("❌ You do not have permission to use this.", ephemeral=True)

    start_time = datetime.now(timezone.utc) + timedelta(minutes=5)
    end_time = start_time + timedelta(hours=1)

    description = f"Host: {host}\nAircraft: {aircraft_type}\nFlight Schedule: {flight_info}\nFlight Code: {flight_code}"

    try:
        event = await interaction.guild.create_scheduled_event(
            name=f"Jet2 Flight - {flight_code}",
            description=description,
            start_time=start_time,
            end_time=end_time,
            entity_type=discord.EntityType.external,
            location="Jet2 Airport",
            privacy_level=discord.PrivacyLevel.guild_only
        )
        await interaction.response.send_message(f"✅ Flight event created for **{flight_code}**\n[View Event]({event.url})")
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to create event: `{e}`", ephemeral=True)

@tree.command(name="flight_announce", description="Announce a Jet2 flight", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    time="Flight time",
    flight_info="Flight route",
    aircraft="Aircraft used",
    airport_link="Link to airport",
    flight_code="Flight code",
    channel_id="Channel ID to announce in"
)
async def flight_announce(interaction: discord.Interaction, time: str, flight_info: str, aircraft: str, airport_link: str, flight_code: str, channel_id: str):
    if ANNOUNCE_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("❌ You do not have permission to use this.", ephemeral=True)

    channel = bot.get_channel(int(channel_id))
    if not channel:
        return await interaction.response.send_message("❌ Invalid channel ID.", ephemeral=True)

    embed = discord.Embed(title=":airplane: FLIGHT ANNOUNCEMENT", description=f"There is a flight today at {time}. We will be operating the {aircraft}.\n\nThis flight will be from {flight_info}.\n\nWe hope to see you attend **{flight_code}**!\n\n[Join Airport]({airport_link})", color=0x8b2828)
    embed.set_image(url=BANNER_URL)
    embed.set_footer(text=generate_footer())

    await channel.send("@everyone")
    await channel.send(embed=embed)
    await interaction.response.send_message("✅ Flight announcement sent.", ephemeral=True)

@tree.command(name="infract", description="Issue a staff infraction", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    user="User to infract",
    reason="Reason for the infraction",
    type="Type (Termination / Infraction / Demotion)",
    demotion_role="Role they were demoted from (optional)"
)
async def infract(interaction: discord.Interaction, user: discord.Member, reason: str, type: str, demotion_role: str = "N/A"):
    if interaction.channel_id != ALLOWED_CHANNEL_ID or INFRACT_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("❌ You cannot use this command here or lack permissions.", ephemeral=True)

    embed = discord.Embed(title="Infraction Notice", description=f"**Infracted User:** {user.mention}\n**Infracted By:** {interaction.user.mention}\n**Type:** {type}\n**Reason:** {reason}\n**Previous Role:** {demotion_role}", color=0x8b2828)
    embed.set_image(url=BANNER_URL)
    embed.set_footer(text=generate_footer())

    await interaction.channel.send(f"{user.mention}", embed=embed)
    await interaction.response.send_message("✅ Infraction logged.", ephemeral=True)

@tree.command(name="promote", description="Promote a staff member", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    user="User to promote",
    promotion_to="New role/title",
    reason="Reason for promotion"
)
async def promote(interaction: discord.Interaction, user: discord.Member, promotion_to: str, reason: str):
    if interaction.channel_id != ALLOWED_CHANNEL_ID or PROMOTE_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("❌ You cannot use this command here or lack permissions.", ephemeral=True)

    embed = discord.Embed(title="Promotion Notice", description=f"**Promoted User:** {user.mention}\n**Promoted By:** {interaction.user.mention}\n**New Position:** {promotion_to}\n**Reason:** {reason}", color=0x8b2828)
    embed.set_image(url=BANNER_URL)
    embed.set_footer(text=generate_footer())

    await interaction.channel.send(f"{user.mention}", embed=embed)
    await interaction.response.send_message("✅ Promotion logged. Check your DMs.", ephemeral=True)

@tree.command(name="flight_log", description="Log a Jet2 flight session", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    user="User to log",
    evidence="Image evidence",
    session_date="Date of session",
    flight_code="Flight code"
)
async def flight_log(interaction: discord.Interaction, user: discord.Member, evidence: discord.Attachment, session_date: str, flight_code: str):
    if interaction.channel_id != ALLOWED_CHANNEL_ID or LOG_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("❌ You cannot use this command here or lack permissions.", ephemeral=True)

    if not evidence.content_type.startswith('image/'):
        return await interaction.response.send_message("❌ Please upload an image for evidence.", ephemeral=True)

    embed = discord.Embed(title="Flight Log", description=f"**Logged User:** {user.mention}\n**Logged By:** {interaction.user.mention}\n**Date:** {session_date}\n**Flight Code:** {flight_code}", color=0x8b2828)
    embed.set_image(url=evidence.url)
    embed.set_footer(text=generate_footer())

    await interaction.channel.send(f"{user.mention}", embed=embed)
    await interaction.response.send_message("✅ Flight log saved. Check your DMs.", ephemeral=True)

bot.run(TOKEN)
