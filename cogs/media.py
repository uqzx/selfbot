import asyncio
import urllib.parse
import aiohttp
import discord
from discord.ext import commands

class Media(commands.Cog):
    def __init__(self, client):
        self.client = client

    async def _cleanup(self, ctx):
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="lyrics", aliases=["l"])
    async def lyrics(self, ctx, *, query: str = None):
        """fetch song lyrics using lrclib api"""
        await self._cleanup(ctx)
        if not query:
            return

        url = f"https://lrclib.net/api/search?q={urllib.parse.quote(query)}"
        headers = {"user-agent": "selfbot v2.5"}
        msg = await ctx.send(f"```\n[*] searching lyrics for '{query}'...\n```")

        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status != 200:
                        await msg.edit(content="```\n[!] lyrics search failed\n```")
                        await asyncio.sleep(4)
                        await msg.delete()
                        return

                    data = await resp.json()
                    if not data or not isinstance(data, list) or len(data) == 0:
                        await msg.edit(content="```\n[!] no lyrics found\n```")
                        await asyncio.sleep(4)
                        await msg.delete()
                        return

                    track = data[0]
                    title = track.get("trackName", "unknown")
                    artist = track.get("artistName", "unknown")
                    album = track.get("albumName", "unknown")
                    plain_lyrics = track.get("plainLyrics")

                    if not plain_lyrics:
                        await msg.edit(content=f"```\n[!] track found ({title} - {artist}), but lyrics are instrumental or unavailable\n```")
                        await asyncio.sleep(6)
                        await msg.delete()
                        return

                    lines = plain_lyrics.strip().split("\n")
                    trimmed_lyrics = "\n".join(lines[:25])
                    if len(lines) > 25:
                        trimmed_lyrics += "\n\n...[truncated due to length]"

                    out = (
                        "```\n"
                        f"--- lyrics: {title} by {artist} ({album}) ---\n\n"
                        f"{trimmed_lyrics}\n"
                        "```"
                    )
                    await msg.edit(content=out)
                    await asyncio.sleep(30)
                    try:
                        await msg.delete()
                    except Exception:
                        pass
        except Exception:
            await msg.edit(content="```\n[!] error connecting to lyrics api\n```")
            await asyncio.sleep(4)
            try:
                await msg.delete()
            except Exception:
                pass

    @commands.command(name="spotify", aliases=["sp", "track"])
    async def spotify_lookup(self, ctx, member: discord.Member = None):
        """view detailed spotify track status and progress bar"""
        await self._cleanup(ctx)
        target = member or ctx.author
        
        spotify_activity = None
        for activity in target.activities:
            if isinstance(activity, discord.Spotify):
                spotify_activity = activity
                break

        if not spotify_activity:
            await ctx.send(f"```\n[!] {target.name} is not listening to spotify\n```", delete_after=5)
            return

        now = discord.utils.utcnow()
        start = spotify_activity.start
        end = spotify_activity.end
        
        progress_str = "n/a"
        if start and end:
            total_duration = (end - start).total_seconds()
            elapsed = (now - start).total_seconds()
            progress = max(0.0, min(1.0, elapsed / total_duration))
            
            bar_length = 15
            filled = int(bar_length * progress)
            bar = "█" * filled + "░" * (bar_length - filled)
            
            cur_min, cur_sec = divmod(int(elapsed), 60)
            tot_min, tot_sec = divmod(int(total_duration), 60)
            progress_str = f"[{bar}] {cur_min:02d}:{cur_sec:02d} / {tot_min:02d}:{tot_sec:02d}"

        out = (
            "```\n"
            f"--- spotify info: {target.name} ---\n"
            f"song:       {spotify_activity.title}\n"
            f"artist(s):  {', '.join(spotify_activity.artists)}\n"
            f"album:      {spotify_activity.album}\n"
            f"progress:   {progress_str}\n"
            f"track url:  [https://open.spotify.com/track/](https://open.spotify.com/track/){spotify_activity.track_id}\n"
            "```"
        )
        await ctx.send(out, delete_after=20)
        if spotify_activity.album_cover_url:
            await ctx.send(spotify_activity.album_cover_url, delete_after=20)

    @commands.command(name="albumart", aliases=["art", "cover"])
    async def album_art(self, ctx, member: discord.Member = None):
        """grab album cover image of currently playing spotify track"""
        await self._cleanup(ctx)
        target = member or ctx.author
        
        for activity in target.activities:
            if isinstance(activity, discord.Spotify) and activity.album_cover_url:
                await ctx.send(activity.album_cover_url, delete_after=15)
                return

        await ctx.send(f"```\n[!] no album cover found for {target.name}\n```", delete_after=4)

    @commands.command(name="artistsearch", aliases=["artist", "asr"])
    async def artist_search(self, ctx, *, artist_name: str = None):
        """search tracks by artist name using lrclib"""
        await self._cleanup(ctx)
        if not artist_name:
            return

        url = f"https://lrclib.net/api/search?artist_name={urllib.parse.quote(artist_name)}"
        headers = {"user-agent": "selfbot v2.5"}
        msg = await ctx.send(f"```\n[*] searching tracks by '{artist_name}'...\n```")

        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status != 200:
                        await msg.edit(content="```\n[!] artist search failed\n```")
                        await asyncio.sleep(4)
                        await msg.delete()
                        return

                    data = await resp.json()
                    if not data or not isinstance(data, list) or len(data) == 0:
                        await msg.edit(content="```\n[!] no tracks found for this artist\n```")
                        await asyncio.sleep(4)
                        await msg.delete()
                        return

                    tracks = data[:10]
                    lines = [f" - {t.get('trackName')} ({t.get('albumName', 'unknown album')})" for t in tracks]

                    out = (
                        "```\n"
                        f"--- artist search: {artist_name} ---\n"
                        + "\n".join(lines) +
                        "\n```"
                    )
                    await msg.edit(content=out)
                    await asyncio.sleep(25)
                    try:
                        await msg.delete()
                    except Exception:
                        pass
        except Exception:
            await msg.edit(content="```\n[!] artist search error\n```")
            await asyncio.sleep(4)
            try:
                await msg.delete()
            except Exception:
                pass

async def setup(client):
    await client.add_cog(Media(client))