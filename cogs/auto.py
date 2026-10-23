import asyncio
import random
import discord
from discord.ext import commands, tasks

class Auto(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.autodel_delay = None
        self.autodel_channels = set()
        self.auto_reactions = {}  # keyword -> emoji
        self.target_reacts = {}   # user_id -> emoji
        self.auto_responses = {}  # trigger -> reply
        self.active_typing = set()
        self.status_list = []
        self.status_loop.start()

    def cog_unload(self):
        self.status_loop.cancel()

    async def _cleanup(self, ctx):
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @tasks.loop(minutes=5)
    async def status_loop(self):
        if not self.status_list:
            return
        try:
            status = random.choice(self.status_list)
            await self.client.change_presence(activity=discord.Game(name=status))
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id == self.client.user.id:
            if self.autodel_delay and message.channel.id in self.autodel_channels:
                asyncio.create_task(self._delayed_delete(message, self.autodel_delay))
            return

        content = message.content.lower()

        # target user auto reaction
        if message.author.id in self.target_reacts:
            try:
                await message.add_reaction(self.target_reacts[message.author.id])
            except Exception:
                pass

        # keyword auto reaction
        for kw, emoji in self.auto_reactions.items():
            if kw in content:
                try:
                    await message.add_reaction(emoji)
                except Exception:
                    pass

        # auto responses
        for trig, reply in self.auto_responses.items():
            if trig in content:
                try:
                    await message.channel.send(reply, delete_after=10)
                except Exception:
                    pass

    @commands.Cog.listener()
    async def on_relationship_add(self, relationship):
        if relationship.type == discord.RelationshipType.incoming_request:
            try:
                await relationship.user.accept()
            except Exception:
                pass

    async def _delayed_delete(self, message, delay):
        await asyncio.sleep(delay)
        try:
            await message.delete()
        except Exception:
            pass

    @commands.command(name="autodel")
    async def autodel(self, ctx, seconds: int = 0):
        """auto-deletes your sent messages after x seconds"""
        await self._cleanup(ctx)
        if seconds <= 0:
            self.autodel_channels.discard(ctx.channel.id)
            await ctx.send("```\n[✔] auto-del disabled for channel\n```", delete_after=3)
        else:
            self.autodel_channels.add(ctx.channel.id)
            self.autodel_delay = seconds
            await ctx.send(f"```\n[✔] auto-del enabled ({seconds}s)\n```", delete_after=4)

    @commands.command(name="autoreact", aliases=["ar"])
    async def autoreact(self, ctx, mode: str = None, target: str = None, emoji: str = None):
        """advanced auto-react (.ar word <keyword> <emoji> or .ar user <userid> <emoji>)"""
        await self._cleanup(ctx)
        if not mode:
            out = (
                "```\n"
                "--- autoreact menu ---\n"
                ".ar word <keyword> <emoji>\n"
                ".ar user <user_id> <emoji>\n"
                ".ar list\n"
                "```"
            )
            await ctx.send(out, delete_after=10)
            return

        m = mode.lower()
        if m == "word" and target and emoji:
            self.auto_reactions[target.lower()] = emoji
            await ctx.send(f"```\n[✔] keyword react set: {target} -> {emoji}\n```", delete_after=4)
        elif m == "user" and target and emoji:
            try:
                uid = int(target)
                self.target_reacts[uid] = emoji
                await ctx.send(f"```\n[✔] user react set: {uid} -> {emoji}\n```", delete_after=4)
            except ValueError:
                await ctx.send("```\n[!] invalid user id\n```", delete_after=3)
        elif m == "list":
            words = ", ".join(self.auto_reactions.keys()) or "none"
            users = ", ".join(str(u) for u in self.target_reacts.keys()) or "none"
            await ctx.send(f"```\nwords: {words}\nusers: {users}\n```", delete_after=10)

    @commands.command(name="autostatus")
    async def autostatus(self, ctx, action: str = None, *, status_text: str = None):
        """rotates status messages (.autostatus add <text> or clear)"""
        await self._cleanup(ctx)
        if not action:
            await ctx.send("```\n[!] use .autostatus add <text> or clear\n```", delete_after=4)
            return
        act = action.lower()
        if act == "add" and status_text:
            self.status_list.append(status_text)
            await ctx.send(f"```\n[✔] added status rotation\n```", delete_after=4)
        elif act == "clear":
            self.status_list.clear()
            await ctx.send("```\n[✔] cleared statuses\n```", delete_after=3)

    @commands.command(name="autotyping")
    async def autotyping(self, ctx):
        """keeps typing indicator active"""
        await self._cleanup(ctx)
        cid = ctx.channel.id
        if cid in self.active_typing:
            self.active_typing.remove(cid)
            await ctx.send("```\n[✔] auto typing off\n```", delete_after=3)
        else:
            self.active_typing.add(cid)
            await ctx.send("```\n[✔] auto typing on\n```", delete_after=4)
            while cid in self.active_typing:
                try:
                    async with ctx.channel.typing():
                        await asyncio.sleep(8)
                except Exception:
                    break

async def setup(client):
    await client.add_cog(Auto(client))