import asyncio
import discord
from discord.ext import commands

class Rpc(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.app_id = None
        self.activity_type = discord.ActivityType.playing
        self.name = "discord.py"
        self.details = None
        self.state = None
        self.large_image = None
        self.small_image = None
        self.stream_url = "https://twitch.tv/twitch"

    async def _cleanup(self, ctx):
        try:
            await ctx.message.delete()
        except Exception:
            pass

    def _format_image(self, img):
        if not img:
            return None
        img = img.strip()
        if img.startswith("mp:") or (len(img) < 30 and "." not in img):
            return img
        if img.startswith("https://"):
            return "mp:external/https/" + img[8:]
        if img.startswith("http://"):
            return "mp:external/http/" + img[7:]
        return img

    async def _update_rpc(self, ctx=None):
        if not self.name and not self.app_id:
            return

        assets = {}
        if self.large_image:
            assets["large_image"] = self._format_image(self.large_image)
        if self.small_image:
            assets["small_image"] = self._format_image(self.small_image)

        kwargs = {
            "type": self.activity_type,
            "name": self.name or "custom rpc"
        }
        if self.details:
            kwargs["details"] = self.details
        if self.state:
            kwargs["state"] = self.state
        if self.app_id:
            try:
                kwargs["application_id"] = int(self.app_id)
            except ValueError:
                pass
        if assets:
            kwargs["assets"] = assets
        if self.activity_type == discord.ActivityType.streaming:
            kwargs["url"] = self.stream_url

        try:
            activity = discord.Activity(**kwargs)
            await self.client.change_presence(activity=activity)
        except Exception as e:
            if ctx:
                await ctx.send(f"```\n[!] rpc update error: {e}\n```", delete_after=5)

    @commands.command(name="rpc")
    async def rpc_command(self, ctx, subcmd: str = None, *, arg: str = None):
        """ultimate custom rich presence manager"""
        await self._cleanup(ctx)
        
        if not subcmd:
            out = (
                "```\n"
                "--- rpc manager syntax ---\n"
                ".rpc <playing|streaming|listening|watching|competing> <name>\n"
                ".rpc 2 <second line text>\n"
                ".rpc id <application id>\n"
                ".rpc large <image link, asset key, or upload attachment>\n"
                ".rpc small <same | image link | asset key | upload attachment>\n"
                ".rpc refresh\n"
                ".rpc clear\n"
                "```"
            )
            await ctx.send(out, delete_after=15)
            return

        sub = subcmd.lower()

        if sub == "clear":
            self.app_id = None
            self.name = None
            self.details = None
            self.state = None
            self.large_image = None
            self.small_image = None
            await self.client.change_presence(activity=None)
            await ctx.send("```\n[✔] rpc cleared successfully\n```", delete_after=3)
            return

        if sub == "refresh":
            await self._update_rpc(ctx)
            await ctx.send("```\n[✔] rpc presence refreshed\n```", delete_after=3)
            return

        if sub == "2":
            if not arg:
                await ctx.send("```\n[!] provide text for second line\n```", delete_after=3)
                return
            self.details = arg
            await self._update_rpc(ctx)
            await ctx.send(f"```\n[✔] rpc details set: {arg}\n```", delete_after=4)
            return

        if sub == "id":
            if not arg or not arg.strip().isdigit():
                await ctx.send("```\n[!] invalid application id\n```", delete_after=4)
                return
            self.app_id = arg.strip()
            await self._update_rpc(ctx)
            await ctx.send(f"```\n[✔] rpc application id set: {self.app_id}\n```", delete_after=4)
            return

        if sub in ["large", "largeimage"]:
            img = None
            if ctx.message.attachments:
                img = ctx.message.attachments[0].url
            elif arg:
                img = arg.replace("image", "", 1).strip()
            
            if not img:
                await ctx.send("```\n[!] provide an image link, key, or attach an image\n```", delete_after=4)
                return
            
            self.large_image = img
            await self._update_rpc(ctx)
            await ctx.send(f"```\n[✔] rpc large image updated\n```", delete_after=4)
            return

        if sub in ["small", "smallimage"]:
            img = None
            if arg and "same" in arg.lower():
                img = self.large_image
            elif ctx.message.attachments:
                img = ctx.message.attachments[0].url
            elif arg:
                img = arg.replace("image", "", 1).strip()

            if not img:
                await ctx.send("```\n[!] provide 'same', an image link, key, or attachment\n```", delete_after=4)
                return

            self.small_image = img
            await self._update_rpc(ctx)
            await ctx.send(f"```\n[✔] rpc small image updated\n```", delete_after=4)
            return

        type_map = {
            "playing": discord.ActivityType.playing,
            "streaming": discord.ActivityType.streaming,
            "listening": discord.ActivityType.listening,
            "watching": discord.ActivityType.watching,
            "competing": discord.ActivityType.competing
        }

        if sub in type_map:
            self.activity_type = type_map[sub]
            if arg:
                self.name = arg
            await self._update_rpc(ctx)
            await ctx.send(f"```\n[✔] rpc type set to {sub}: {self.name}\n```", delete_after=4)
            return

        full_name = f"{subcmd} {arg}" if arg else subcmd
        self.name = full_name
        await self._update_rpc(ctx)
        await ctx.send(f"```\n[✔] rpc status name set: {self.name}\n```", delete_after=4)

async def setup(client):
    await client.add_cog(Rpc(client))