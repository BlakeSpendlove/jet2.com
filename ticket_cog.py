import discord
from discord.ext import commands
from discord import app_commands

class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.support_forum_id = int(bot.support_forum_id)  # We'll set this from main bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("TicketCog loaded")

    @commands.Cog.listener()
    async def on_message(self, message):
        # Only respond to DMs, ignore bot messages
        if message.guild is None and not message.author.bot:
            # Create ticket in the forum
            forum = self.bot.get_channel(self.support_forum_id)
            if forum is None:
                print("Support forum channel not found.")
                return

            # Create a new thread (forum post)
            thread = await forum.create_thread(
                name=f"Support Ticket - {message.author.display_name}",
                content=f"New support ticket from {message.author.mention}\n\n**Message:** {message.content}"
            )

            # Ping @everyone who can see the forum (forum handles permissions)
            await thread.send("@everyone")

            # Confirm to user
            await message.channel.send(f"Hi {message.author.name}, your support ticket has been created: {thread.jump_url}")

    @app_commands.command(name="claim", description="Claim a support ticket")
    @app_commands.guilds()  # optionally specify your guild(s)
    async def claim(self, interaction: discord.Interaction):
        # This command must be used inside a forum thread (ticket)
        if not isinstance(interaction.channel, discord.Thread):
            await interaction.response.send_message("You can only claim a ticket inside the ticket thread.", ephemeral=True)
            return

        thread = interaction.channel

        # Check if already claimed
        if thread.owner_id == interaction.user.id:
            await interaction.response.send_message("You have already claimed this ticket.", ephemeral=True)
            return

        # Claim the ticket by setting the owner to this user
        await thread.edit(owner=interaction.user)

        # Send confirmation message inside the ticket thread
        await thread.send(f"Ticket claimed by {interaction.user.mention}")

        # Respond to interaction
        await interaction.response.send_message(f"You have claimed this ticket.", ephemeral=True)


async def setup(bot):
    # Pass the forum channel ID as a bot attribute (optional)
    bot.support_forum_id = bot.support_forum_id  # this will be set in main bot

    await bot.add_cog(TicketCog(bot))
