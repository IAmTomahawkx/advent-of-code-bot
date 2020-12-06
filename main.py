import asyncio
import pathlib
import datetime
import traceback

import aiohttp
import asyncpg
import ujson
import colorama
import discord
from discord.ext import commands

from utils import board, tz

colorama.init(autoreset=True, wrap=True)

class AOCBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        pth = pathlib.Path("settings.json")
        if pth.exists():
            with pth.open("r") as f:
                self.config = ujson.load(f)
        else:
            with pth.open("w") as f:
                f.write(ujson.dumps({
                    "token": "",
                    "prefix": "!",
                    "db": "postgres://"
                }))
            print(colorama.Fore.RED + "Please fill out the settings.json file, and rerun the bot")
            raise SystemExit(1)

        super(AOCBot, self).__init__(*args, command_prefix=self.get_pre, description="I do cool things", **kwargs)

        self.lock = asyncio.Lock()
        self.session = None
        self.board_cache = {}

    async def start(self, *args, **kwargs):
        self.session = aiohttp.ClientSession()
        self.db = await asyncpg.create_pool(self.config['db'], min_size=1, max_inactive_connection_lifetime=10)
        await super(AOCBot, self).start(*args, **kwargs)
        await self.session.close()

    async def get_pre(self, _, msg):
        return commands.when_mentioned_or(self.config['prefix'])(self, msg)

    async def get_board(self, board_id, cookie, force=False, seconds=15*60) -> board.Board:
        if board_id in self.board_cache:
            if not force and (datetime.datetime.utcnow() - self.board_cache[board_id].fetched).total_seconds() < seconds:
                return self.board_cache[board_id]

        async with self.session.get(f"https://adventofcode.com/2020/leaderboard/private/view/{board_id}.json", headers={"cookie": cookie}) as resp:
            resp.raise_for_status()
            data = await resp.json(loads=ujson.loads) # noqa

        b = board.Board(data)
        self.board_cache[board_id] = b
        return b

    async def on_command_error(self, context, exception):
        if isinstance(exception, commands.CommandNotFound):
            return

        elif isinstance(exception, commands.MissingPermissions):
            return await context.send(f"You are missing {', '.join(exception.missing_perms)} permissions")

        elif isinstance(exception, commands.NoPrivateMessage):
            return await context.send("This command can only be used in a server")

        await super(AOCBot, self).on_command_error(context, exception)
        await context.send("Something screwed up: " + ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__)))

intents = discord.Intents.default()
intents.members = True
bot = AOCBot(allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=False), intents=intents)

@bot.command(aliases=['hello'])
async def about(ctx):
    if not bot.owner_id and not bot.owner_ids:
        await bot.is_owner(ctx.author) # get the owner

    owner = bot.owner_ids or [bot.owner_id]
    fmt = f"Made by IAmTomahawkx#1000 (547861735391100931).\nThis bot is being run by {', '.join(f'<@!{x}>' for x in owner)}\n Just your average discord bot. "
    now = tz.get()
    if now.month == 12 and now.day < 26:
        fmt += f"\nIt is currently day {now.day} of Advent of code"

    await ctx.send(fmt)

@bot.command()
async def invite(ctx):
    """
    gives you a link to invite this bot
    """
    await ctx.send(embed=discord.Embed(description=f"You can invite me [Here]({discord.utils.oauth_url(bot.user.id)})", colour=0x2F3136))

bot.load_extension("cogs.aoc")
bot.load_extension("cogs.reminder")
bot.load_extension("jishaku")
bot.run(bot.config['token'])
