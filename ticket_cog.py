import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
import datetime

class TicketView(View):
    def __init__(self, cog, thread, user_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.thread = thread
        self.user_id = user_id
        self.claimed_by = None

        self.claim_button = Button(label="Claim Ticket", style=discord.ButtonStyle.primary)
        self.claim_button.callback = self.claim_callback
        self.add_item(self.claim_button)

    async def claim_callback(self, interaction: discord.Interaction):
        if self.claimed_by is not None:
            await interaction.response.send_message(f"Ticket already claimed by <@{self.claimed_by}>.", ephemeral=True)
            return
        self.claimed_by = interaction.user.id
        self.claim_button.disabled = True
        await interaction.response.edit_message(view=self)
        await self.thread.send(f"Ticket claimed by {interaction.user.mention}")
        # Save claim info in the cog's mapping
        self.cog.claimed_tickets[self.thread.id] = self.claimed_by

class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.support_forum_id = getattr(bot, "SUPPORT_FORUM_ID", None)
        self.user_to_thread = {}  # user_id -> thread object
        self.thread_to_user = {}  # thread_id -> user_id
        self.claimed_tickets = {}  # thread_id -> staff user id

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"TicketCog loaded. Support forum ID: {self.support_forum_id}")

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore bot messages, except for forum staff responses below
        if message.author.bot:
            return

        # 1) Handle DMs from users to create or send in tickets
        if isinstance(message.channel, discord.DMChannel):
            user = message.author
            # Check if user already has a ticket thread open
            thread = self.user_to_thread.get(user.id)
            forum = self.bot.get_channel(self.support_forum_id)
            if thread is None:
                # Create new ticket thread in forum
                thread = await forum.create_thread(
                    name=f"ticket-{user.name}-{user.discriminator}",
                    type=discord.ChannelType.public_thread,
                    auto_archive_duration=1440,
                    reason=f"Support ticket opened by {user}"
                )
                # Store mappings
                self.user_to_thread[user.id] = thread
                self.thread_to_user[thread.id] = user.id

                # Send initial message with claim button
                view = TicketView(self, thread, user.id)
                embed = discord.Embed(title="New Support Ticket",
                                      description=f"Ticket opened by {user.mention} (ID: {user.id})",
                                      color=discord.Color.blue())
                embed.add_field(name="Instructions",
                                value="Support staff can claim this ticket by pressing the **Claim Ticket** button below.")
                await thread.send(embed=embed, view=view)

                # DM user confirmation
                confirm_embed = discord.Embed(
                    title="Ticket Opened",
                    description="Thank you for contacting support! Your ticket has been opened. You will receive updates here within 24 hours.",
                    color=discord.Color.green(),
                    timestamp=datetime.datetime.utcnow()
                )
                await user.send(embed=confirm_embed)

            else:
                # Existing thread - send user message into thread
                # Relay plain message text + attachments
                content = message.content or ""
                files = [await f.to_file() for f in message.attachments] if message.attachments else []
                await thread.send(f"**User:** {content}", files=files)

            return

        # 2) Handle staff messages inside forum threads, relay to user as embed
        if message.guild and message.channel.id in self.thread_to_user:
            thread = message.channel
            user_id = self.thread_to_user[thread.id]
            user = self.bot.get_user(user_id)
            if user is None:
                # User not found? Remove mappings
                del self.thread_to_user[thread.id]
                for k, v in list(self.user_to_thread.items()):
                    if v.id == thread.id:
                        del self.user_to_thread[k]
                        break
                return

            # Don't relay user messages from user themselves (only staff)
            if message.author.id == user_id:
                return

            # Create embed for staff reply
            embed = discord.Embed(description=message.content, color=discord.Color.blue(), timestamp=datetime.datetime.utcnow())
            embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
            if message.attachments:
                embed.set_image(url=message.attachments[0].url)
            try:
                await user.send(embed=embed)
            except discord.Forbidden:
                # Can't DM user - maybe blocked bot
                await thread.send(f"⚠️ Cannot DM {user.mention}.")
            return

    @app_commands.command(name="ticket_close", description="Close the ticket you're managing")
    async def ticket_close(self, interaction: discord.Interaction):
        channel = interaction.channel
        if not channel or channel.id not in self.thread_to_user:
            await interaction.response.send_message("This command can only be used inside a ticket thread.", ephemeral=True)
            return

        # Only the staff who claimed it can close or admins (you can expand this check)
        claimed_by = self.claimed_tickets.get(channel.id)
        if claimed_by is None or (claimed_by != interaction.user.id and not interaction.user.guild_permissions.manage_threads):
            await interaction.response.send_message("Only the staff member who claimed this ticket or moderators can close it.", ephemeral=True)
            return

        user_id = self.thread_to_user[channel.id]
        user = self.bot.get_user(user_id)
        closer_name = str(interaction.user)

        # Delete thread
        await interaction.response.send_message("Closing ticket and notifying user...")
        await channel.delete()

        # Clean mappings
        del self.thread_to_user[channel.id]
        if user_id in self.user_to_thread:
            del self.user_to_thread[user_id]
        if channel.id in self.claimed_tickets:
            del self.claimed_tickets[channel.id]

        # DM user
        if user:
            embed = discord.Embed(title="Ticket Closed",
                                  description=f"Your support ticket was closed by **{closer_name}** at {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}.",
                                  color=discord.Color.red(),
                                  timestamp=datetime.datetime.utcnow())
            try:
                await user.send(embed=embed)
            except discord.Forbidden:
                # User has DMs disabled
                pass

    @ticket_close.error
    async def ticket_close_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message(f"Error closing ticket: {error}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketCog(bot))
