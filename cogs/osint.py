import asyncio
import hashlib
import urllib.parse
import aiohttp
import discord
from discord.ext import commands

class Osint(commands.Cog):
    def __init__(self, client):
        self.client = client

    async def _cleanup(self, ctx):
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="osintuser", aliases=["ousr", "socials"])
    async def osint_user(self, ctx, username: str = None):
        """scan username across platforms"""
        await self._cleanup(ctx)
        if not username:
            return

        platforms = {
            "github": f"https://github.com/{username}",
            "twitter": f"https://twitter.com/{username}",
            "instagram": f"https://instagram.com/{username}",
            "reddit": f"https://reddit.com/user/{username}",
            "tiktok": f"https://tiktok.com/@{username}",
            "twitch": f"https://twitch.tv/{username}",
            "steam": f"https://steamcommunity.com/id/{username}",
            "soundcloud": f"https://soundcloud.com/{username}",
            "telegram": f"https://t.me/{username}"
        }

        msg = await ctx.send(f"```\n[*] scanning platforms for '{username}'...\n```")
        results = []
        headers = {"user-agent": "mozilla/5.0"}

        async with aiohttp.ClientSession(headers=headers) as session:
            for name, url in platforms.items():
                try:
                    async with session.get(url, timeout=4) as resp:
                        if resp.status == 200:
                            results.append(f"[+] {name}: found")
                        else:
                            results.append(f"[-] {name}: not found")
                except Exception:
                    results.append(f"[!] {name}: timeout")
                await asyncio.sleep(0.2)

        out = f"```\n--- osint user: {username} ---\n" + "\n".join(results) + "\n```"
        await msg.edit(content=out)
        await asyncio.sleep(25)
        try:
            await msg.delete()
        except Exception:
            pass

    @commands.command(name="breach", aliases=["xon", "checkbreach"])
    async def breach_lookup(self, ctx, email: str = None):
        """check email breaches via xposedornot api"""
        await self._cleanup(ctx)
        if not email:
            return

        url = f"https://api.xposedornot.com/v1/check-email/{email.strip()}"
        msg = await ctx.send(f"```\n[*] querying xposedornot for {email}...\n```")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        breaches = data.get("breaches", [])
                        if breaches and len(breaches) > 0 and breaches[0]:
                            flat_breaches = []
                            for item in breaches:
                                if isinstance(item, list):
                                    flat_breaches.extend(item)
                                else:
                                    flat_breaches.append(str(item))
                            
                            out = (
                                "```\n"
                                f"--- xposedornot breach check: {email} ---\n"
                                f"status: exposed! total breaches: {len(flat_breaches)}\n"
                                + "\n".join([f" - {b}" for b in flat_breaches]) + "\n```"
                            )
                        else:
                            out = f"```\n[✔] clean! no known breaches found for {email}\n```"
                        
                        await msg.edit(content=out)
                        await asyncio.sleep(25)
                        try:
                            await msg.delete()
                        except Exception:
                            pass
                    else:
                        await msg.edit(content="```\n[!] email not found in breach database or api error\n```")
                        await asyncio.sleep(4)
                        try:
                            await msg.delete()
                        except Exception:
                            pass
        except Exception:
            await msg.edit(content="```\n[!] xposedornot api connection error\n```")
            await asyncio.sleep(4)
            try:
                await msg.delete()
            except Exception:
                pass

    @commands.command(name="osintip", aliases=["oip"])
    async def osint_ip(self, ctx, ip: str = None):
        """deep ip lookup, asn, isp, and geo"""
        await self._cleanup(ctx)
        if not ip:
            return

        url = f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,zip,lat,lon,timezone,isp,org,as,query"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    data = await resp.json()
                    if data.get("status") == "success":
                        out = (
                            "```\n"
                            f"--- osint ip: {data.get('query')} ---\n"
                            f"country:  {data.get('country')} ({data.get('regionName')}, {data.get('city')})\n"
                            f"zip/tz:   {data.get('zip')} | {data.get('timezone')}\n"
                            f"coords:   {data.get('lat')}, {data.get('lon')}\n"
                            f"isp/org:  {data.get('isp')} / {data.get('org')}\n"
                            f"asn:      {data.get('as')}\n"
                            "```"
                        )
                        await ctx.send(out, delete_after=25)
                    else:
                        await ctx.send("```\n[!] invalid ip or failed lookup\n```", delete_after=4)
        except Exception:
            await ctx.send("```\n[!] api error during ip recon\n```", delete_after=4)

    @commands.command(name="subdomains", aliases=["crtsh", "subs"])
    async def subdomains(self, ctx, domain: str = None):
        """crt.sh subdomain enumeration"""
        await self._cleanup(ctx)
        if not domain:
            return

        url = f"https://crt.sh/?q=%25.{domain}&output=json"
        msg = await ctx.send(f"```\n[*] querying crt.sh for {domain}...\n```")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=12) as resp:
                    if resp.status != 200:
                        await msg.edit(content="```\n[!] crt.sh query failed\n```")
                        await asyncio.sleep(4)
                        await msg.delete()
                        return
                    
                    data = await resp.json()
                    subs = set()
                    for entry in data:
                        name_value = entry.get("name_value", "")
                        for sub in name_value.split("\n"):
                            if sub and "*" not in sub:
                                subs.add(sub.strip().lower())

                    subs_list = sorted(list(subs))[:18]
                    count = len(subs)

                    out = (
                        "```\n"
                        f"--- crt.sh recon: {domain} (total: {count}) ---\n"
                        + "\n".join([f" -> {s}" for s in subs_list])
                        + ("\n ...and more" if count > 18 else "") + "\n```"
                    )
                    await msg.edit(content=out)
                    await asyncio.sleep(25)
                    try:
                        await msg.delete()
                    except Exception:
                        pass
        except Exception:
            await msg.edit(content="```\n[!] error querying crt.sh api\n```")
            await asyncio.sleep(4)
            try:
                await msg.delete()
            except Exception:
                pass

    @commands.command(name="dig")
    async def dig(self, ctx, domain: str = None, record_type: str = "A"):
        """dns dig lookup via cloudflare doh"""
        await self._cleanup(ctx)
        if not domain:
            return

        url = f"https://cloudflare-dns.com/dns-query?name={domain}&type={record_type.upper()}"
        headers = {"accept": "application/dns-json"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    data = await resp.json()
                    answers = data.get("Answer", [])
                    
                    if not answers:
                        await ctx.send(f"```\n[!] no {record_type.upper()} records found\n```", delete_after=5)
                        return

                    records = [ans.get("data") for ans in answers]
                    out = (
                        "```\n"
                        f"--- dig {record_type.upper()}: {domain} ---\n"
                        + "\n".join([f" {r}" for r in records])
                        + "\n```"
                    )
                    await ctx.send(out, delete_after=20)
        except Exception:
            await ctx.send("```\n[!] dig query error\n```", delete_after=4)

    @commands.command(name="nslookup")
    async def nslookup(self, ctx, domain: str = None):
        """complete multi-record dns sweep"""
        await self._cleanup(ctx)
        if not domain:
            return

        types = ["A", "AAAA", "MX", "NS", "TXT"]
        headers = {"accept": "application/dns-json"}
        results = [f"--- nslookup sweep: {domain} ---"]

        async with aiohttp.ClientSession() as session:
            for r_type in types:
                url = f"https://cloudflare-dns.com/dns-query?name={domain}&type={r_type}"
                try:
                    async with session.get(url, headers=headers) as resp:
                        data = await resp.json()
                        answers = data.get("Answer", [])
                        if answers:
                            for ans in answers:
                                results.append(f"[{r_type}] {ans.get('data')}")
                        else:
                            results.append(f"[{r_type}] none")
                except Exception:
                    results.append(f"[{r_type}] error")
                await asyncio.sleep(0.1)

        out = "```\n" + "\n".join(results) + "\n```"
        await ctx.send(out, delete_after=25)

    @commands.command(name="mac")
    async def mac_lookup(self, ctx, mac: str = None):
        """lookup mac address vendor"""
        await self._cleanup(ctx)
        if not mac:
            return

        url = f"https://api.macvendors.com/{mac}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        vendor = await resp.text()
                        await ctx.send(f"```\n[mac lookup] {mac} -> {vendor}\n```", delete_after=15)
                    else:
                        await ctx.send(f"```\n[!] vendor not found or invalid mac\n```", delete_after=5)
        except Exception:
            await ctx.send("```\n[!] mac api error\n```", delete_after=4)

    @commands.command(name="hashtype", aliases=["hash"])
    async def hash_type(self, ctx, *, text: str = None):
        """identify hash type by string length"""
        await self._cleanup(ctx)
        if not text:
            return

        length = len(text.strip())
        guesses = {
            32: "md5 / ntlm",
            40: "sha-1 / mysql5",
            64: "sha-256 / blake2s",
            96: "sha-384",
            128: "sha-512 / whirlpool"
        }
        match = guesses.get(length, "unknown / custom length")
        out = f"```\n[hash id] length: {length} | type guess: {match}\n```"
        await ctx.send(out, delete_after=15)

    @commands.command(name="gravatar")
    async def gravatar(self, ctx, email: str = None):
        """lookup gravatar profile by email address"""
        await self._cleanup(ctx)
        if not email:
            return

        clean_email = email.strip().lower()
        email_hash = hashlib.md5(clean_email.encode()).hexdigest()
        url = f"https://www.gravatar.com/{email_hash}.json"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        entry = data.get("entry", [{}])[0]
                        display_name = entry.get("displayName", "unknown")
                        profile_url = entry.get("profileUrl", "none")
                        out = (
                            "```\n"
                            f"--- gravatar recon: {email} ---\n"
                            f"name:    {display_name}\n"
                            f"profile: {profile_url}\n"
                            f"avatar:  [https://www.gravatar.com/avatar/](https://www.gravatar.com/avatar/){email_hash}\n"
                            "```"
                        )
                        await ctx.send(out, delete_after=20)
                    else:
                        await ctx.send("```\n[!] no gravatar profile found for this email\n```", delete_after=5)
        except Exception:
            await ctx.send("```\n[!] gravatar api error\n```", delete_after=4)

    @commands.command(name="ports", aliases=["scan"])
    async def portscan(self, ctx, host: str = None):
        """quick tcp port scanner"""
        await self._cleanup(ctx)
        if not host:
            return

        common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 3306, 3389, 8080]
        msg = await ctx.send(f"```\n[*] scanning common ports on {host}...\n```")
        open_ports = []

        for port in common_ports:
            try:
                _, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=1.5)
                open_ports.append(port)
                writer.close()
                await writer.wait_closed()
            except Exception:
                continue

        out = (
            "```\n"
            f"--- port scan: {host} ---\n"
            + (f"open ports: {', '.join(map(str, open_ports))}" if open_ports else "no common ports open")
            + "\n```"
        )
        await msg.edit(content=out)
        await asyncio.sleep(20)
        try:
            await msg.delete()
        except Exception:
            pass

async def setup(client):
    await client.add_cog(Osint(client))