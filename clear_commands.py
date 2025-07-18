import discord
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

class ClearClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = discord.app_commands.CommandTree(self)

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        # Remove ALL global commands
        await self.tree.sync()
        await self.tree.clear_commands()
        await self.tree.sync()
        print("✅ Global slash commands cleared.")
        await self.close()

client = ClearClient()
client.run(TOKEN)
