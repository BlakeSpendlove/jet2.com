import discord
from discord.ext import commands
from discord import ui
import os
import random
import string

GUILD_ID = int(os.getenv("GUILD_ID"))
SUPPORT_FORUM_ID = int(os.getenv("SUPPORT_FORUM_ID"))

# Helper to generate ticket IDs
def generate_ticket_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

class TicketView(ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=None)
        self.author_id = author_id

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.success, custom_id="claim_button")
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"<@{interaction.user.id}> has claimed this ticket.", ephemeral=False)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_button")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.delete()

class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if not isinstance(message.channel, discord.DMChannel):
            return

        if message.author == self.bot.user:
            return

        guild = self.bot.get_guild(GUILD_ID)
        forum = guild.get_channel(SUPPORT_FORUM_ID)

        if not forum:
            await message.channel.send("⚠️ Support forum not found. Please try again later.")
            return

        ticket_id = generate_ticket_id()

        # Create forum post
        thread = await forum.create_thread(
            name=f"Ticket from {message.author.name} [{ticket_id}]",
            content=f"**User:** {message.author.mention}\n**Message:** {message.content}",
            reason="New support ticket",
        )

        await thread.send(f"<@everyone> New ticket from {message.author.mention}!", view=TicketView(message.author.id))

        await message.channel.send(
            f"🎫 Your support request has been received!\nSomeone will respond within **24 hours**.\n**Ticket ID:** `{ticket_id}`."
        )

def setup(bot):
    bot.add_cog(TicketCog(bot))
