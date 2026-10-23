import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, client):
        self.client = client

    async def _cleanup(self, ctx):
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="help", aliases=["cmds", "commands"])
    async def help_menu(self, ctx, cog_name: str = None):
        """display available selfbot cogs and commands"""
        await self._cleanup(ctx)

        # if no cog specified, list all active cogs
        if not cog_name:
            cogs = [c.lower() for c in self.client.cogs.keys()]
            out = (
                "```\n"
                "--- selfbot help menu ---\n"
                f"active cogs: {', '.join(cogs)}\n\n"
                "usage: `,help <cog>`\n"
                "example: `,help utility` or `,help osint`\n"
                "```"
            )
            await ctx.send(out, delete_after=15)
            return

        # find target cog (case-insensitive search)
        target_cog = None
        for name, cog in self.client.cogs.items():
            if name.lower() == cog_name.lower():
                target_cog = cog
                break

        if not target_cog:
            await ctx.send(f"```\n[!] cog '{cog_name}' not found\n```", delete_after=4)
            return

        cmds = target_cog.get_commands()
        cmd_lines = []
        for cmd in cmds:
            aliases = f" [{', '.join(cmd.aliases)}]" if cmd.aliases else ""
            desc = f" -> {cmd.help}" if cmd.help else ""
            cmd_lines.append(f"  ,{cmd.name}{aliases}{desc}")

        out = (
            "```\n"
            f"--- {cog_name.lower()} module commands ---\n"
            + "\n".join(cmd_lines)
            + "\n```"
        )
        await ctx.send(out, delete_after=20)

async def setup(client):
    await client.add_cog(Help(client))