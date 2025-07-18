import os
import discord
from discord.ext import commands
from discord.ui import Button, View
from dotenv import load_dotenv
import datetime
import uuid

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
SUPPORT_FORUM_ID = int(os.getenv("SUPPORT_FORUM_ID"))
GUILD_ID = int(os.getenv("GUILD_ID"))
ALLOWED_CHANNEL_ID = int(os.getenv("ALLOWED_CHANNEL_ID"))  # For Jet2 logs etc.

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

open_tickets = {}

class TicketView(View):
    def __init__(self, author_id):
        super().__init__(timeout=None)
        self.author_id = author_id

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.primary, custom_id="claim_button")
    async def claim(self, interaction: discord.Interaction, button: Button):
        if not interaction.channel:
            return
        await interaction.response.send_message(f"{interaction.user.mention} has claimed this ticket!", ephemeral=False)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_button")
    async def close(self, interaction: discord.Interaction, button: Button):
        if not interaction.channel:
            return
        await interaction.response.send_message("This ticket has been closed.")
        await interaction.channel.delete()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    bot.add_view(TicketView(author_id=0))  # persistent view registration

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if isinstance(message.channel, discord.DMChannel):
        guild = bot.get_guild(GUILD_ID)
        if not guild:
            print("Guild not found")
            return

        support_forum = guild.get_channel(SUPPORT_FORUM_ID)
        if not support_forum or not isinstance(support_forum, discord.ForumChannel):
            print("Support forum not found or not a forum")
            return

        # Check if user already has an open ticket
        if message.author.id in open_tickets:
            thread = open_tickets[message.author.id]
            await thread.send(f"**{message.author.name}:** {message.content}")
            await message.channel.send("Your message has been forwarded to the support team.")
            return

        # Create a new thread in the forum
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        thread_title = f"Ticket from {message.author.name}"
        thread = await support_forum.create_thread(
            name=thread_title,
            content=f"**User:** {message.author.mention} ({message.author.id})\n**Issue:** {message.content}\n\nOpened at <t:{int(datetime.datetime.now().timestamp())}:f>",
        )

        open_tickets[message.author.id] = thread

        view = TicketView(author_id=message.author.id)
        await thread.send(f"Support team, a new ticket has been opened.", view=view)

        await message.channel.send(
            "✅ Your support request has been received. A staff member will respond within 24 hours."
        )
    else:
        await bot.process_commands(message)

# Example placeholder command from the Jet2 system
@bot.command()
async def flight_log(ctx):
    if ctx.channel.id != ALLOWED_CHANNEL_ID:
        await ctx.send("You can't use this command here.")
        return
    await ctx.send("Flight log submitted. ✅")

bot.run(TOKEN)
