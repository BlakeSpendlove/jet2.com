import discord
from discord.ext import commands
import os
import random
import string

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

BANNER_URL = os.getenv('BANNER_URL')
PROMOTE_CHANNEL_ID = int(os.getenv('PROMOTE_CHANNEL_ID', 0))
INFRACT_CHANNEL_ID = int(os.getenv('INFRACT_CHANNEL_ID', 0))
FLIGHT_LOG_CHANNEL_ID = int(os.getenv('FLIGHT_LOG_CHANNEL_ID', 0))

def get_footer():
    return "ID: " + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def check_channel(ctx, allowed_channel_id):
    return ctx.channel.id == allowed_channel_id

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command(name='flight_schedule')
async def flight_schedule(ctx, flight_code: str, date: str):
    embed = discord.Embed(
        title="Flight Scheduled",
        description=f"{ctx.author.mention} has scheduled flight **{flight_code}** for {date}.",
        color=0x3498db
    )
    embed.set_thumbnail(url=BANNER_URL)
    embed.set_footer(text=get_footer())
    await ctx.send(embed=embed)

@bot.command(name='flight_announce')
async def flight_announce(ctx, flight_code: str, status: str):
    embed = discord.Embed(
        title="Flight Announcement",
        description=f"Flight **{flight_code}** status updated: **{status}**",
        color=0xe67e22
    )
    embed.set_thumbnail(url=BANNER_URL)
    embed.set_footer(text=get_footer())
    await ctx.send(embed=embed)

@bot.command(name='promote')
async def promote(ctx, member: discord.Member, new_role: str):
    if not check_channel(ctx, PROMOTE_CHANNEL_ID):
        await ctx.send(f"This command can only be used in the designated promote channel.")
        return

    role = discord.utils.get(ctx.guild.roles, name=new_role)
    if role is None:
        await ctx.send(f"Role '{new_role}' not found.")
        return
    await member.add_roles(role)
    embed = discord.Embed(
        title="Promotion",
        description=f"{member.mention} was promoted to **{new_role}** by {ctx.author.mention}.",
        color=0x2ecc71
    )
    embed.set_thumbnail(url=BANNER_URL)
    embed.set_footer(text=get_footer())
    await ctx.send(embed=embed)

@bot.command(name='infract')
async def infract(ctx, member: discord.Member, *, reason: str):
    if not check_channel(ctx, INFRACT_CHANNEL_ID):
        await ctx.send(f"This command can only be used in the designated infract channel.")
        return

    embed = discord.Embed(
        title="Infraction Issued",
        description=f"{member.mention} was given an infraction for:\n{reason}\nBy {ctx.author.mention}.",
        color=0xe74c3c
    )
    embed.set_thumbnail(url=BANNER_URL)
    embed.set_footer(text=get_footer())
    await ctx.send(embed=embed)

@bot.command(name='flight_log')
async def flight_log(ctx, flight_code: str, *, log_details: str):
    if not check_channel(ctx, FLIGHT_LOG_CHANNEL_ID):
        await ctx.send(f"This command can only be used in the designated flight log channel.")
        return

    embed = discord.Embed(
        title="Flight Log Entry",
        description=f"Log for flight **{flight_code}**:\n{log_details}",
        color=0x9b59b6
    )
    embed.set_thumbnail(url=BANNER_URL)
    embed.set_footer(text=get_footer())
    await ctx.send(embed=embed)

@bot.command(name='view_logs')
async def view_logs(ctx, member: discord.Member):
    # Example placeholder logs; replace with your real data retrieval
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
    await ctx.send(embed=embed)

bot.run(os.getenv('DISCORD_TOKEN'))
