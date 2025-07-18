import discord
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

class ClearClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = discord.app_commands.CommandTree(self)

    async def on_ready(self):
        print(f"Logged in as {self.user}. Clearing guild commands...")
        guild = discord.Object(id=GUILD_ID)
        await self.tree.clear_commands(guild=guild)
        print("Cleared all guild commands.")
        await self.close()

client = ClearClient()
client.run(TOKEN)
