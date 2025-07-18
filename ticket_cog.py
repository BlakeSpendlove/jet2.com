import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
import datetime
import asyncio

TICKET_LOG = {}  # Maps user_id to forum thread

class TicketView(View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id

        self.claimed_by = None

        self.add_item(ClaimButton(self))
        self.add_item(CloseButton(self))

class ClaimButton(Button):
    def __init__(self, parent_view):
        super().__init__(label="Claim", style=discord.ButtonStyle.primary)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if self.parent_view.claimed_by:
            await interaction.response.send_message(f"Ticket already claimed by <@{self.parent_view.claimed_by}>.", ephemeral=True)
        else:
            self.parent_view.claimed_by = interaction.user.id
            await interaction.response.send_message(f"You have claimed this ticket.", ephemeral=True)
            await interaction.message.channel.send(f"<@{interaction.user.id}> has claimed this ticket.")

class CloseButton(Button):
    def __init__(self, parent_view):
        super().__init__(label="Close Ticket", style=discord.ButtonStyle.danger)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        user_id = self.parent_view.user_id
        user = await interaction.client.fetch_user(user_id)

        embed = discord.Embed(title="Ticket Closed",
                              description=f"Your ticket has been closed by **{interaction.user.name}**.",
                              color=discord.Color.red())
        embed.set_footer(text=f"Closed at {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")

        try:
            await user.send(embed=embed)
        except:
            pass

        if interaction.channel:
            await interaction.channel.delete()

class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if isinstance(message.channel, discord.DMChannel):
            if message.author.id in TICKET_LOG:
                thread = TICKET_LOG[message.author.id]
                await thread.send(f"**{message.author}**: {message.content}")
            else:
                guild = discord.utils.get(self.bot.guilds)
                support_forum = guild.get_channel(int(self.bot.SUPPORT_FORUM_ID))

                thread = await support_forum.create_thread(
                    name=f"Ticket from {message.author.name}",
                    content=f"**User:** {message.author.mention}\n**Message:** {message.content}"
                )

                TICKET_LOG[message.author.id] = thread

                await thread.send(f"New ticket opened by {message.author.mention}.",
                                  view=TicketView(message.author.id))

                try:
                    await message.author.send(
                        "Thank you for your message. A support ticket has been opened. Our team will respond within 24 hours."
                    )
                except:
                    pass

        elif message.channel.id in [t.id for t in TICKET_LOG.values()]:
            for user_id, thread in TICKET_LOG.items():
                if thread.id == message.channel.id:
                    user = await self.bot.fetch_user(user_id)
                    embed = discord.Embed(title=f"Message from Support",
                                          description=message.content,
                                          color=discord.Color.blue())
                    embed.set_footer(text=f"By {message.author} | {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
                    try:
                        await user.send(embed=embed)
                    except:
                        pass

    @app_commands.command(name="ticket_close", description="Close the current ticket.")
    async def ticket_close(self, interaction: discord.Interaction):
        for user_id, thread in TICKET_LOG.items():
            if thread.id == interaction.channel.id:
                del TICKET_LOG[user_id]
                await interaction.channel.delete()
                return
        await interaction.response.send_message("This channel is not a registered ticket.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketCog(bot))
