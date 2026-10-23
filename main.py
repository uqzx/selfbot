import asyncio
import os
import discord
from discord.ext import commands

def load_prefix():
    if os.path.exists("prefix.txt"):
        with open("prefix.txt", "r") as f:
            p = f.read().strip()
            return p if p else ","
    return ","

async def get_prefix(bot, message):
    return load_prefix()

client = commands.Bot(
    command_prefix=get_prefix,
    self_bot=True,
    help_command=None
)

@client.event
async def on_ready():
    print(f"[+] logged in as: {client.user}")
    print(f"[+] active prefix: {load_prefix()}")
    print("-" * 35)

async def load_cogs():
    if not os.path.exists("cogs"):
        os.makedirs("cogs")
        return
        
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            cog_name = filename[:-3]
            try:
                await client.load_extension(f"cogs.{cog_name}")
                print(f"[+] loaded cog: {cog_name}")
            except Exception as e:
                print(f"[-] failed to load {cog_name}: {e}")

async def main():
    async with client:
        await load_cogs()
        token = "xx"
        await client.start(token)

if __name__ == "__main__":
    asyncio.run(main())