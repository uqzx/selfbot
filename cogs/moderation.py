import asyncio
import random
import sys
import discord
from discord.ext import commands

class Moderation(commands.Cog):
    def __init__(self, client):
        self.client = client

    # helper to safely delete trigger message
    async def _cleanup(self, ctx):
        try:
            await ctx.message.delete()
        except Exception:
            pass

    # --- ADVANCED PURGE SYSTEM ---

    @commands.command(name="purge", aliases=["clear", "c", "p"])
    async def purge(self, ctx, amount: str = None):
        """purge your own messages (amount or 'all')"""
        await self._cleanup(ctx)
        if not amount or not self.client.user:
            return

        is_all = amount.lower() == "all"
        fetch_limit = 5000 if is_all else int(amount) if amount.isdigit() else 0
        if fetch_limit <= 0:
            return

        print(f"[*] scanning history in #{ctx.channel} (limit: {fetch_limit})...")
        deleted = 0
        target_count = float("inf") if is_all else int(amount)
        my_id = self.client.user.id

        try:
            async for msg in ctx.channel.history(limit=fetch_limit):
                if deleted >= target_count:
                    break

                if msg and msg.author and msg.author.id == my_id:
                    try:
                        await msg.delete()
                        deleted += 1
                        sys.stdout.write(f"\r[+] purged: {deleted} messages")
                        sys.stdout.flush()
                        await asyncio.sleep(random.uniform(0.18, 0.32))
                    except discord.HTTPException as e:
                        if e.status == 429:
                            await asyncio.sleep(getattr(e, "retry_after", 2.5))
                        else:
                            continue
                    except Exception:
                        continue

            print(f"\n[✔] finished! total deleted: {deleted}\n")
        except Exception as e:
            print(f"\n[-] purge error: {e}")

    @commands.command(name="puser", aliases=["purgeuser", "pu"])
    async def purge_user(self, ctx, member: discord.Member = None, amount: int = 50):
        """purge messages from a specific user (requires mod perms)"""
        await self._cleanup(ctx)
        if not member:
            return

        deleted = 0
        async for msg in ctx.channel.history(limit=500):
            if deleted >= amount:
                break
            if msg and msg.author and msg.author.id == member.id:
                try:
                    await msg.delete()
                    deleted += 1
                    await asyncio.sleep(0.2)
                except Exception:
                    continue
        print(f"[✔] purged {deleted} messages from {member}")

    @commands.command(name="pcontains", aliases=["pcontain", "pc"])
    async def purge_contains(self, ctx, word: str = None, amount: int = 50):
        """purge your messages containing a specific keyword"""
        await self._cleanup(ctx)
        if not word:
            return

        deleted = 0
        my_id = self.client.user.id
        async for msg in ctx.channel.history(limit=500):
            if deleted >= amount:
                break
            if msg and msg.author and msg.author.id == my_id and word.lower() in (msg.content or "").lower():
                try:
                    await msg.delete()
                    deleted += 1
                    await asyncio.sleep(0.2)
                except Exception:
                    continue
        print(f"[✔] purged {deleted} messages containing '{word}'")

    @commands.command(name="plinks", aliases=["pl"])
    async def purge_links(self, ctx, amount: int = 50):
        """purge your messages that contain links"""
        await self._cleanup(ctx)
        deleted = 0
        my_id = self.client.user.id
        async for msg in ctx.channel.history(limit=500):
            if deleted >= amount:
                break
            if msg and msg.author and msg.author.id == my_id:
                if "http://" in msg.content or "https://" in msg.content:
                    try:
                        await msg.delete()
                        deleted += 1
                        await asyncio.sleep(0.2)
                    except Exception:
                        continue

    @commands.command(name="pfiles", aliases=["pf"])
    async def purge_files(self, ctx, amount: int = 50):
        """purge your messages containing files or attachments"""
        await self._cleanup(ctx)
        deleted = 0
        my_id = self.client.user.id
        async for msg in ctx.channel.history(limit=500):
            if deleted >= amount:
                break
            if msg and msg.author and msg.author.id == my_id and msg.attachments:
                try:
                    await msg.delete()
                    deleted += 1
                    await asyncio.sleep(0.2)
                except Exception:
                    continue

    # --- CHANNEL MANAGEMENT ---

    @commands.command(name="nuke")
    async def nuke(self, ctx):
        """clone and delete channel to completely reset it"""
        await self._cleanup(ctx)
        if not isinstance(ctx.channel, discord.TextChannel):
            return

        try:
            channel = ctx.channel
            pos = channel.position
            new_channel = await channel.clone(reason="selfbot channel nuke")
            await channel.delete()
            await new_channel.edit(position=pos)
            msg = await new_channel.send("```\n[✔] channel nuked\n```")
            await asyncio.sleep(3)
            await msg.delete()
        except Exception as e:
            print(f"[-] nuke error: {e}")

    @commands.command(name="lock")
    async def lock(self, ctx):
        """lock down channel @everyone send permissions"""
        await self._cleanup(ctx)
        if not isinstance(ctx.channel, discord.TextChannel):
            return

        try:
            overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
            overwrite.send_messages = False
            await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            await ctx.send("```\n[lock] channel locked\n```", delete_after=4)
        except Exception as e:
            print(f"[-] lock error: {e}")

    @commands.command(name="unlock")
    async def unlock(self, ctx):
        """unlock channel @everyone send permissions"""
        await self._cleanup(ctx)
        if not isinstance(ctx.channel, discord.TextChannel):
            return

        try:
            overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
            overwrite.send_messages = True
            await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            await ctx.send("```\n[unlock] channel unlocked\n```", delete_after=4)
        except Exception as e:
            print(f"[-] unlock error: {e}")

    @commands.command(name="slowmode", aliases=["sm"])
    async def slowmode(self, ctx, seconds: int = 0):
        """set channel slowmode delay"""
        await self._cleanup(ctx)
        if not isinstance(ctx.channel, discord.TextChannel):
            return

        try:
            await ctx.channel.edit(slowmode_delay=seconds)
            await ctx.send(f"```\n[slowmode] set to {seconds}s\n```", delete_after=4)
        except Exception as e:
            print(f"[-] slowmode error: {e}")

    # --- SERVER GUILD MODERATION ---

    @commands.command(name="kick")
    async def kick(self, ctx, member: discord.Member = None, *, reason: str = "no reason specified"):
        """kick member from server"""
        await self._cleanup(ctx)
        if not member:
            return
        try:
            await member.kick(reason=reason)
            await ctx.send(f"```\n[✔] kicked {member.name}\n```", delete_after=4)
        except Exception as e:
            print(f"[-] kick error: {e}")

    @commands.command(name="ban")
    async def ban(self, ctx, member: discord.Member = None, *, reason: str = "no reason specified"):
        """ban member from server"""
        await self._cleanup(ctx)
        if not member:
            return
        try:
            await member.ban(reason=reason, delete_message_days=0)
            await ctx.send(f"```\n[✔] banned {member.name}\n```", delete_after=4)
        except Exception as e:
            print(f"[-] ban error: {e}")

    @commands.command(name="unban")
    async def unban(self, ctx, user_id: int = None):
        """unban user by ID"""
        await self._cleanup(ctx)
        if not user_id:
            return
        try:
            user = await self.client.fetch_user(user_id)
            await ctx.guild.unban(user)
            await ctx.send(f"```\n[✔] unbanned {user.name}\n```", delete_after=4)
        except Exception as e:
            print(f"[-] unban error: {e}")

async def setup(client):
    await client.add_cog(Moderation(client))