import difflib
from typing import Optional, Union

import asyncpg
import tabulate
import discord
from discord.ext import commands
import discord.ext.commands.core

from utils import tz, time, board as _board

def setup(bot):
    bot.add_cog(Leaderboard(bot))

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("languages.txt") as f:
            self.langs = f.read().splitlines(False)

    @commands.command("cookie", aliases=['set-cookie'])
    @commands.has_guild_permissions(manage_guild=True)
    async def guild_cookie(self, ctx):
        """
        sets the given cookie as the guilds cookie.
        DO NOT SEND YOUR COOKIE IN CHAT, the bot will ask you for it in dms!

        You can delete your cookie at any time by using the rmcookie command
        """
        today = tz.get()
        await ctx.send(f"{ctx.author.mention}, please DM me your cookie. This can be found by going to "
                       f"https://adventofcode.com/{today.year}/leaderboard/private while logged in, opening the "
                       "inspector, and grabbing the `cookie` header from the page request. This will overwrite an existing cookie from this server", allowed_mentions=discord.AllowedMentions(users=True))

        try:
            msg = await self.bot.wait_for("message", timeout=60, check=lambda m: m.guild is None and m.author.id == ctx.author.id)
        except:
            return await ctx.send("Took too long, aborting")

        cookie = msg.content.strip()
        if not cookie.startswith("session="):
            cookie = f"session={cookie}"

        async with self.bot.session.get(f"https://adventofcode.com/{today.year}/leaderboard/private", headers={"cookie": cookie}, allow_redirects=False) as resp:
            if resp.status != 200:
                return await ctx.send("Invalid cookie")

        await self.bot.db.execute("INSERT INTO cookies VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET cookie = $2", ctx.guild.id, cookie)
        await ctx.author.send(f"Your cookie will now be used for {ctx.guild.name}")

    @commands.command("rmcookie", aliases=['remove-cookie'])
    @commands.has_guild_permissions(manage_guild=True)
    async def remove_cookie(self, ctx):
        """
        removes your servers cookie and leaderboard number.
        User associations and language counters are unaffected
        """
        await ctx.send("Confirm deletion of your server's cookie and leaderboard id?")
        try:
            msg = await self.bot.wait_for("message",
                                          check=lambda m: m.channel == ctx.channel and m.author == ctx.author,
                                          timeout=30)
        except:
            return await ctx.send("Failed to respond in time...")
        try:
            if commands.core._convert_to_bool(msg.content):
                await self.bot.db.execute("DELETE FROM cookies CASCADE WHERE guild_id = $1")
                await ctx.send("Deleted all data on your server's cookie and leaderboard id")
            else:
                await ctx.send("Aborting")
        except:
            await ctx.send("Aborting")

    @commands.group(aliases=['board'], invoke_without_command=True)
    @commands.guild_only()
    async def leaderboard(self, ctx: commands.Context):
        """
        shows the top 5 users on your server's leaderboard
        """
        board_id = await self.bot.db.fetchrow("SELECT board_id, cookie FROM guilds inner join cookies c on guilds.guild_id = c.guild_id where guilds.guild_id = $1", ctx.guild.id)
        if not board_id:
            return await ctx.send("Please ask someone with the manage server permission to set a board id")

        board = await self.bot.get_board(board_id['board_id'], board_id['cookie'])
        sorts = board.sort_by_local_board
        vals = []
        for ind, member in enumerate(sorts[0:5], start=1):
            vals.append((member.stars, member.local_score, member.name))

        v = tabulate.tabulate(vals, headers=("Stars \U00002b50", "board points", "name"), tablefmt="simple", stralign="center")
        e = discord.Embed(title=f"{board.owner.name}'s leaderboard", description="```\n" + v.strip() + "\n```")
        await ctx.send(embed=e)

    @leaderboard.command()
    @commands.has_guild_permissions(manage_guild=True)
    @commands.guild_only()
    async def set(self, ctx: commands.Context, board_id: int):
        """
        sets the server's board to the given leaderboard id
        """
        cookie = await self.bot.db.fetchval("SELECT cookie FROM cookies WHERE guild_id = $1", ctx.guild.id)
        if not cookie:
            return await ctx.send(f"You need to set a cookie for your server first, use the {ctx.prefix}cookie command (do not send your cookie in chat)")
        try:
            await self.bot.get_board(board_id, cookie)
        except:
            await ctx.send("You do not have permission to view this board, or it does not exist")
        else:
            await self.bot.db.execute("INSERT INTO guilds VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET board_id = $2", ctx.guild.id, board_id)
            await ctx.send(f"Saved the server's board id as {board_id}")

    @commands.command(cooldown_after_parsing=True)
    @commands.cooldown(1, 10000, commands.BucketType.user)
    @commands.guild_only()
    async def iam(self, ctx: commands.Context, user_id: Optional[int], *, name: str = None):
        """
        associates your discord user with your advent of code user.
        Give your user id or your name (the name displayed on adventofcode.com)
        """
        if not user_id and not name:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You did not pass a user id or a name")

        board_id = await self.bot.db.fetchrow("SELECT board_id, cookie FROM guilds inner join cookies c on c.guild_id = guilds.guild_id where guilds.guild_id = $1", ctx.guild.id)
        if not board_id:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("Please ask someone with the manage server permission to set a board id")

        board = await self.bot.get_board(board_id['board_id'], board_id['cookie'])

        if user_id:
            user = discord.utils.get(board.members, id=user_id)
            if not user:
                ctx.command.reset_cooldown(ctx)
                return await ctx.send("That user id could not be found. Are you sure you're in this server's leaderboard?")

        else:
            names = [x.name for x in board.members if x.name is not None]
            closest = difflib.get_close_matches(name, names, 1) # yes this is blocking, no i dont care
            if not closest:
                ctx.command.reset_cooldown(ctx)
                return await ctx.send("No names matched...")

            closest = closest[0]
            await ctx.send(f"{ctx.author.mention}, confirm name of {closest}", allowed_mentions=discord.AllowedMentions(users=True))
            try:
                msg = await self.bot.wait_for("message", check=lambda m: m.channel == ctx.channel and m.author == ctx.author, timeout=30)
            except:
                return await ctx.send("Failed to respond in time...")

            try:
                if commands.core._convert_to_bool(msg.content):
                    user = discord.utils.get(board.members, name=closest)
                else:
                    ctx.command.reset_cooldown(ctx)
                    return await ctx.send("Aborting")
            except:
                ctx.command.reset_cooldown(ctx)
                return await ctx.send("Aborting")

        await self.bot.db.execute("INSERT INTO users VALUES ($1, $2) ON CONFLICT (discord_id) DO UPDATE SET aoc_id = $2", ctx.author.id, user.id)
        await ctx.send(f"Confirmed {ctx.author.mention} as {user.name} with AOC id {user.id}")

    @commands.command()
    @commands.guild_only()
    async def lang(self, ctx, day: Optional[int], language: str, file_link: str = None):
        """
        tells the bot that youve completed todays challenge in the given language
        """
        if language not in self.langs:
            closest = difflib.get_close_matches(language, self.langs, 3)
            return await ctx.send(f"That language was not recognized (the closest found were {', '.join(closest)}). Tell the bot owner to add it to the languages.txt file")

        today = tz.get()
        day = day or today.day
        if today.month != 12:
            return await ctx.send("It's not AOC time yet")

        if day > 25:
            return await ctx.send("Hmm, that doesnt seem like a valid day")

        try:
            await self.bot.db.execute("INSERT INTO langs VALUES ($1, $2, $3, $4)", ctx.author.id, day, language, file_link)
        except asyncpg.UniqueViolationError:
            return await ctx.send("You have already done that language today...")
        except asyncpg.ForeignKeyViolationError:
            return await ctx.send("You have not confirmed your AOC id...")
        else:
            await ctx.send(f"Marked {language} as completed for day {day}")

    @commands.command()
    @commands.guild_only()
    async def info(self, ctx, user: Union[discord.User, str]=None):
        """
        gives you advent of code info on the given person. if no target is given, will give you your own info
        """
        user = user or ctx.author
        if isinstance(user, discord.user.BaseUser):
            query = """
            SELECT * FROM users
            INNER JOIN guilds g on g.guild_id = $2
            INNER JOIN cookies c on c.guild_id = g.guild_id
            WHERE discord_id = $1
            """
            # do this in two queries due to variable row amounts
            data = await self.bot.db.fetchrow(query, user.id, ctx.guild.id)
            if not data:
                return await ctx.send(f"Hmm, either the {'you havent identified yourself' if user == ctx.author else f'{user.name} hasnt identified themselves'} "
                                      f"(use the {ctx.prefix}iam command), the server owner has not set up a leaderboard (use the {ctx.prefix}leaderboard set command), "
                                      f"or something screwed up internally. Probably the latter")

            board = await self.bot.get_board(data['board_id'], data['cookie'])
            langs = await self.bot.db.fetch("SELECT * FROM langs WHERE id = $1", user.id)
            member: _board.Member = discord.utils.get(board.members, id=data['aoc_id'])

        else:
            board_id = await self.bot.db.fetchrow(
                "SELECT board_id, cookie FROM guilds inner join cookies c on c.guild_id = guilds.guild_id where guilds.guild_id = $1",
                ctx.guild.id)
            if not board_id:
                return await ctx.send("Please ask someone with the manage server permission to set a board id")

            board = await self.bot.get_board(board_id['board_id'], board_id['cookie'])
            member = discord.utils.get(board.members, name=user)
            if not member:
                return await ctx.send("That user doesnt appear to be in your server's leaderboard. Passing leaderboard names is case-sensitive")
            langs = []

        rows = []

        for day in range(1, tz.get().day+1):
            day_langs = [x['lang'] for x in langs if x['day'] == day]
            stars = member.completion_stats.get(day)
            if not stars:
                star_1 = "Incomplete"
                star_2 = "Incomplete"
            else:
                start = tz.day_start(day)
                star_1 = time.human_timedelta(stars[1], source=start) if stars[1] else "Incomplete"
                star_2 = time.human_timedelta(stars[2], source=start) if stars[2] else "Incomplete"

            rows.append((day, star_1, star_2, ", ".join(day_langs)))

        table = tabulate.tabulate(rows, headers=("Day #", "First star", "Second star", "Languages used"), tablefmt="plain")
        await ctx.send("```\n" + table + "\n```")