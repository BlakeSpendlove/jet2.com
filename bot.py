import discord
from discord.ext import commands
from discord import app_commands
import os
import random
import string
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

SCHEDULE_ROLE_ID = int(os.getenv("SCHEDULE_ROLE_ID"))
ANNOUNCE_ROLE_ID = int(os.getenv("ANNOUNCE_ROLE_ID"))
INFRACT_ROLE_ID = int(os.getenv("INFRACT_ROLE_ID"))
PROMOTE_ROLE_ID = int(os.getenv("PROMOTE_ROLE_ID"))
LOG_ROLE_ID = int(os.getenv("LOG_ROLE_ID"))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

BANNER_URL = "https://media.discordapp.net/attachments/1395760490982150194/1395769069541789736/Banner1.png"
SCHEDULE_BANNER_URL = "https://media.discordapp.net/attachments/1395760490982150194/1395766076490387597/jet2-and-jet2holidays-logos-1.png"

def random_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"Logged in as {bot.user}!")

@bot.tree.command(name="flight_schedule", description="Schedule a Jet2 flight", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    host="Host of the flight",
    time="Time of the flight (e.g. 18:00 GMT)",
    aircraft="Aircraft used (e.g. B737-800)",
    info_code="Flight info - code (e.g. Bournemouth -> Punta Cana - LS8800)"
)
async def flight_schedule(interaction: discord.Interaction, host: str, time: str, aircraft: str, info_code: str):
    if SCHEDULE_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("You do not have permission to use this.", ephemeral=True)

    try:
        info, code = info_code.rsplit(" - ", 1)
    except ValueError:
        return await interaction.response.send_message("Format error. Use: {flight-info} - {flight-code}", ephemeral=True)

    start_time = datetime.now(timezone.utc) + timedelta(minutes=5)
    end_time = start_time + timedelta(hours=1)

    event = await interaction.guild.create_scheduled_event(
        name=f"Jet2 Flight - {code}",
        description=f"**Host:** {host}\n**Aircraft:** {aircraft}\n**Flight Schedule:** {info}\n**Flight Code:** {code}",
        start_time=start_time,
        end_time=end_time,
        entity_type=discord.EntityType.external,
        location="Jet2 Airport",
        privacy_level=discord.PrivacyLevel.guild_only
    )

    await interaction.response.send_message(
        f"Flight event created for **{code}**. [View Event]({event.url})", ephemeral=False
    )

@bot.tree.command(name="flight_announce", description="Announce a Jet2 flight", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    time="Time of the flight",
    info="Flight info (e.g. Bournemouth -> Punta Cana)",
    aircraft="Aircraft",
    link="Airport link",
    code="Flight code (e.g. LS8800)",
    channel_id="Channel ID to post in"
)
async def flight_announce(interaction: discord.Interaction, time: str, info: str, aircraft: str, link: str, code: str, channel_id: str):
    if ANNOUNCE_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("You do not have permission to use this.", ephemeral=True)

    channel = bot.get_channel(int(channel_id))
    embed = discord.Embed(
        title=":airplane: FLIGHT ANNOUNCEMENT",
        description=f"There is a flight today at {time}. We will be operating the {aircraft}.\nThis flight will be from {info}.\n\nWe hope to see you attend {code}!",
        color=0x8b2828
    )
    embed.set_image(url=BANNER_URL)
    embed.set_footer(text=f"ID: {random_id()}")

    await channel.send(content="@everyone", embed=embed)
    await interaction.response.send_message("Flight announced.", ephemeral=True)

@bot.tree.command(name="infract", description="Discipline a staff member", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="User to infract", reason="Reason", type="Type of action", role="Demotion role (optional)")
async def infract(interaction: discord.Interaction, user: discord.Member, reason: str, type: str, role: str = None):
    if INFRACT_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("You do not have permission to use this.", ephemeral=True)

    embed = discord.Embed(title="Infraction Notice", color=0x8b2828)
    embed.add_field(name="Infraction Type", value=type, inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Infracted By", value=interaction.user.mention, inline=False)
    embed.add_field(name="Infracted User", value=user.mention, inline=False)
    embed.set_image(url=BANNER_URL)
    embed.set_footer(text=f"ID: {random_id()}")

    await interaction.channel.send(content=f"{user.mention}", embed=embed)
    await interaction.response.send_message("Infraction sent.", ephemeral=True)

@bot.tree.command(name="promote", description="Promote a staff member", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="User to promote", promotion_to="New rank", reason="Reason")
async def promote(interaction: discord.Interaction, user: discord.Member, promotion_to: str, reason: str):
    if PROMOTE_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("You do not have permission to use this.", ephemeral=True)

    embed = discord.Embed(title="Promotion Notice", color=0x8b2828)
    embed.add_field(name="Promoted To", value=promotion_to, inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Promoted By", value=interaction.user.mention, inline=False)
    embed.add_field(name="Promoted User", value=user.mention, inline=False)
    embed.set_image(url=BANNER_URL)
    embed.set_footer(text=f"ID: {random_id()}\nCheck your direct messages.")

    await interaction.channel.send(content=f"{user.mention}", embed=embed)
    await interaction.response.send_message("Promotion sent.", ephemeral=True)

@bot.tree.command(name="flight_log", description="Log a flight", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="Who hosted the session", evidence="Upload image", session_date="Date of the session")
async def flight_log(interaction: discord.Interaction, user: discord.Member, evidence: discord.Attachment, session_date: str):
    if LOG_ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("You do not have permission to use this.", ephemeral=True)

    if not evidence.content_type.startswith("image/"):
        return await interaction.response.send_message("Only image files are allowed for evidence.", ephemeral=True)

    embed = discord.Embed(title="Flight Log", color=0x8b2828)
    embed.add_field(name="Session Host", value=user.mention, inline=False)
    embed.add_field(name="Logged By", value=interaction.user.mention, inline=False)
    embed.add_field(name="Date", value=session_date, inline=False)
    embed.set_image(url=evidence.url)
    embed.set_footer(text=f"ID: {random_id()}\nCheck your direct messages.")

    await interaction.channel.send(content=f"{user.mention}", embed=embed)
    await interaction.response.send_message("Flight logged.", ephemeral=True)

bot.run(TOKEN)
