import asyncio
import aiohttp
import psutil
import discord
from discord.ext import commands

class Tools(commands.Cog):
    def __init__(self, client):
        self.client = client

    async def _cleanup(self, ctx):
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="sys", aliases=["system", "vps"])
    async def system_stats(self, ctx):
        """shows vps cpu, ram, and disk usage"""
        await self._cleanup(ctx)
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        out = (
            "```\n"
            f"--- vps system metrics ---\n"
            f"cpu usage:  {cpu}%\n"
            f"ram usage:  {ram.percent}% ({round(ram.used / (1024**3), 2)}gb / {round(ram.total / (1024**3), 2)}gb)\n"
            f"disk usage: {disk.percent}% ({round(disk.used / (1024**3), 2)}gb / {round(disk.total / (1024**3), 2)}gb)\n"
            "```"
        )
        await ctx.send(out, delete_after=12)

    @commands.command(name="shorten", aliases=["short"])
    async def shorten(self, ctx, *, url: str):
        """shortens any url using is.gd"""
        await self._cleanup(ctx)
        api_url = f"https://is.gd/create.php?format=simple&url={url}"
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as resp:
                if resp.status == 200:
                    short = await resp.text()
                    await ctx.send(f"```\n--- url shortener ---\n{short.strip()}\n```", delete_after=15)
                else:
                    await ctx.send("```\n[!] failed to shorten url\n```", delete_after=3)

    @commands.command(name="poll")
    async def poll(self, ctx, *, question: str):
        """creates a quick reaction poll"""
        await self._cleanup(ctx)
        msg = await ctx.send(f"📊 **poll:** {question}")
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")
        await msg.add_reaction("🤷")

    @commands.command(name="translate", aliases=["tr"])
    async def translate(self, ctx, lang: str, *, text: str):
        """translates text to a target language"""
        await self._cleanup(ctx)
        api_url = f"https://api.mymemory.translated.net/get?q={text}&langpair=auto|{lang}"
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    res = data.get("responseData", {}).get("translatedText")
                    if res:
                        await ctx.send(f"```\n--- translation ({lang}) ---\n{res}\n```", delete_after=12)
                        return
                await ctx.send("```\n[!] translation failed\n```", delete_after=3)

async def setup(client):
    await client.add_cog(Tools(client))