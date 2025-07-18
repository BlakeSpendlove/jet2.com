import discord
from discord.ext import commands
from discord.ui import Button, View
from datetime import datetime

class TicketView(View):
    def __init__(self, bot, user_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.green)
    async def claim(self, interaction: discord.Interaction, button: Button):
        # Assign the user who clicked as the ticket manager
        # You can add role checks here if needed
        await interaction.response.send_message(f"Ticket claimed by {interaction.user.mention}.", ephemeral=True)
        # Save the claimer ID on the view to use in close
        self.claimer_id = interaction.user.id

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red)
    async def close(self, interaction: discord.Interaction, button: Button):
        # Only allow the claimer or a manager to close
        if hasattr(self, "claimer_id") and interaction.user.id != self.claimer_id:
            await interaction.response.send_message("Only the ticket claimer can close this ticket.", ephemeral=True)
            return

        channel = interaction.channel
        # Find the user who opened the ticket based on channel topic or name
        user = self.bot.get_user(self.user_id)
        if user:
            embed = discord.Embed(
                title="Ticket Closed",
                description=f"Your ticket was closed by {interaction.user} at {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
                color=discord.Color.red()
            )
            try:
                await user.send(embed=embed)
            except Exception:
                pass

        await channel.delete()

class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_map = {}  # Map user_id to channel_id

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore messages sent by bots
        if message.author.bot:
            return

        # DM from user opens or sends in ticket
        if isinstance(message.channel, discord.DMChannel):
            user_id = message.author.id
            # Check if user already has a ticket channel open
            channel_id = self.ticket_map.get(user_id)

            # Get the forum channel to create threads in
            forum_channel = self.bot.get_channel(self.bot.SUPPORT_FORUM_ID)
            if not forum_channel:
                print("Support forum channel not found")
                return

            # If no ticket exists, create thread
            if channel_id is None:
                thread = await forum_channel.create_thread(
                    name=f"Ticket from {message.author.name}",
                    type=discord.ChannelType.public_thread,
                    reason="New support ticket"
                )
                self.ticket_map[user_id] = thread.id

                # Send initial message embed + buttons
                embed = discord.Embed(
                    title="New Ticket",
                    description=f"Ticket opened by {message.author.mention}\n\nMessage:\n{message.content}",
                    color=discord.Color.blue()
                )
                view = TicketView(self.bot, user_id)
                await thread.send(embed=embed, view=view)

                # Notify user their ticket was created
                await message.channel.send("Thank you! Your ticket has been opened. You will receive an update within 24 hours.")
            else:
                # Send the message to the existing ticket thread
                thread = self.bot.get_channel(channel_id)
                if thread:
                    await thread.send(f"**{message.author.name}**: {message.content}")
                else:
                    # thread deleted or missing, remove mapping
                    self.ticket_map.pop(user_id)
                    await message.channel.send("There was an error finding your ticket. Please try again.")

        # Message sent in a forum thread by a support member (manager replies)
        elif message.channel.type == discord.ChannelType.public_thread:
            # Check if this thread is one of our tickets
            if message.channel.id in self.ticket_map.values():
                # Find which user this ticket belongs to
                user_id = None
                for uid, tid in self.ticket_map.items():
                    if tid == message.channel.id:
                        user_id = uid
                        break
                if user_id is None:
                    return

                user = self.bot.get_user(user_id)
                if user is None:
                    return

                # Avoid infinite loops by ignoring bot messages
                if message.author.bot:
                    return

                # Send the support staff message to the user as an embed DM
                embed = discord.Embed(
                    title=f"Support Reply from {message.author}",
                    description=message.content,
                    color=discord.Color.green(),
                    timestamp=message.created_at
                )
                try:
                    await user.send(embed=embed)
                except Exception:
                    pass

    @commands.command(name="ticket_close")
    async def ticket_close(self, ctx):
        # Only works in a ticket thread
        if ctx.channel.id not in self.ticket_map.values():
            await ctx.send("This command can only be used inside a ticket thread.")
            return

        # Find user who opened ticket
        user_id = None
        for uid, tid in self.ticket_map.items():
            if tid == ctx.channel.id:
                user_id = uid
                break

        if user_id is None:
            await ctx.send("User for this ticket not found.")
            return

        user = self.bot.get_user(user_id)
        if user:
            embed = discord.Embed(
                title="Ticket Closed",
                description=f"Your ticket was closed by {ctx.author} at {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
                color=discord.Color.red()
            )
            try:
                await user.send(embed=embed)
            except Exception:
                pass

        await ctx.channel.delete()
        self.ticket_map.pop(user_id, None)

async def setup(bot):
    await bot.add_cog(TicketCog(bot))
