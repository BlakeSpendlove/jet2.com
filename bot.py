import discord
from discord import app_commands
from discord.ext import commands
import os
import random
import string

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

BANNER_URL = os.getenv('BANNER_URL')
PROMOTE_CHANNEL_ID = int(os.getenv('PROMOTE_CHANNEL_ID', 0))
INFRACT_CHANNEL_ID = int(os.getenv('INFRACT_CHANNEL_ID', 0))
FLIGHT_LOG_CHANNEL_ID = int(os.getenv('FLIGHT_LOG_CHANNEL_ID', 0))

def get_footer():
    return "ID: " + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def check_channel(interaction, allowed_channel_id):
    return interaction.channel.id == allowed_channel_id

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} commands')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

@bot.tree.command(name="flight_schedule", description="Schedule a flight")
@app_commands.describe(flight_code="Flight code", date="Date of flight")
async def flight_schedule(interaction: discord.Interaction, flight_code: str, date: str):
    embed = discord.Embed(
        title="Flight Scheduled",
        description=f"{interaction.user.mention} has scheduled flight **{flight_code}** for {date}.",
        color=0x3498db
    )
    embed.set_thumbnail(url=BANNER_URL)
    embed.set_footer(text=get_footer())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="flight_announce", description="Announce flight status")
@app_commands.describe(flight_code="Flight code", status="Flight status")
async def flight_announce(interaction: discord.Interaction, flight_code: str, status: str):
    embed = discord.Embed(
        title="Flight Announcement",
        description=f"Flight **{flight_code}** status updated: **{status}**",
        color=0xe67e22
    )
    embed.set_thumbnail(url=BANNER_URL)
    embed.set_footer(text=get_footer())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="promote", description="Promote a member")
@app_commands.describe(member="Member to promote", new_role="Role to assign")
async def promote(interaction: discord.Interaction, member: discord.Member, new_role: str):
    if not check_channel(interaction, PROMOTE_CHANNEL_ID):
        await interaction.response.send_message(f"This command can only be used in the designated promote channel.", ephemeral=True)
        return
    role = discord.utils.get(interaction.guild.roles, name=new_role)
    if role is None:
        await interaction.response.send_message(f"Role '{new_role}' not found.", ephemeral=True)
        return
    await member.add_roles(role)
    embed = discord.Embed(
        title="Promotion",
        description=f"{member.mention} was promoted to **{new_role}** by {interaction.user.mention}.",
        color=0x2ecc71
    )
    embed.set_thumbnail(url=BANNER_URL)
    embed.set_footer(text=get_footer())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="infract", description="Issue an infraction")
@app_commands.describe(member="Member to infract", reason="Reason for infraction")
async def infract(interaction: discord.Interaction, member: discord.Member, reason: str):
    if not check_channel(interaction, INFRACT_CHANNEL_ID):
        await interaction.response.send_message(f"This command can only be used in the designated infract channel.", ephemeral=True)
        return
    embed = discord.Embed(
        title="Infraction Issued",
        description=f"{member.mention} was given an infraction for:\n{reason}\nBy {interaction.user.mention}.",
        color=0xe74c3c
    )
    embed.set_thumbnail(url=BANNER_URL)
    embed.set_footer(text=get_footer())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="flight_log", description="Log a flight entry")
@app_commands.describe(flight_code="Flight code", log_details="Details for the log")
async def flight_log(interaction: discord.Interaction, flight_code: str, log_details: str):
    if not check_channel(interaction, FLIGHT_LOG_CHANNEL_ID):
        await interaction.response.send_message(f"This command can only be used in the designated flight log channel.", ephemeral=True)
        return
    embed = discord.Embed(
        title="Flight Log Entry",
        description=f"Log for flight **{flight_code}**:\n{log_details}",
        color=0x9b59b6
    )
    embed.set_thumbnail(url=BANNER_URL)
    embed.set_footer(text=get_footer())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="view_logs", description="View logs for a member")
@app_commands.describe(member="Member to view logs for")
async def view_logs(interaction: discord.Interaction, member: discord.Member):
    # Replace with your actual log fetching logic
    example_logs = [
        {"timestamp": "2025-07-14 10:00", "detail": "Scheduled flight AB123"},
        {"timestamp": "2025-07-15 12:30", "detail": "Issued infraction for late arrival"},
        {"timestamp": "2025-07-16 09:15", "detail": "Promoted to Senior Pilot"},
    ]

    embed = discord.Embed(
        title=f"Session Logs for {member.display_name}",
        color=0x1abc9c
    )
    embed.set_thumbnail(url=BANNER_URL)
    for log in example_logs:
        embed.add_field(name=log["timestamp"], value=log["detail"], inline=False)
    embed.set_footer(text=get_footer())
    await interaction.response.send_message(embed=embed)

bot.run(os.getenv('DISCORD_TOKEN'))
