from discord.ext import commands
import discord

class MainCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx):
        """Simple ping command to test bot responsiveness"""
        await ctx.send("Pong!")

    @commands.command(name="hello")
    async def hello(self, ctx):
        """Say hello"""
        await ctx.send(f"Hello {ctx.author.mention}! How can I assist you today?")

async def setup(bot):
    await bot.add_cog(MainCog(bot))
