import asyncio

import discord
from discord.ext import commands

from utils import tz

def setup(bot):
    bot.add_cog(Reminder(bot))

class Reminder(commands.Cog):
    """
    reminds you daily that AOC is about to start
    """
    def __init__(self, bot):
        self.bot = bot
        self.task = bot.loop.create_task(self.remind_sleeper())

    def cog_unload(self):
        self.task.cancel()

    async def remind_sleeper(self):
        while True:
            start = tz.day_start(tz.get().day+1)
            if start.day > 25 or start.month != 12 or (start-tz.get()).total_seconds() < 300:
                await asyncio.sleep(600)
                continue

            await asyncio.sleep((start-tz.get()).total_seconds() - 300)
            await asyncio.shield(self.remind_action(), loop=self.bot.loop)


    async def remind_action(self):
        offset = tz.human_timedelta(tz.day_start(tz.get().day+1), source=tz.get())
        mentions = await self.bot.db.fetch("SELECT * FROM reminders")

        channels = {} # group the channels to bulk send messages
        for m in mentions:
            if m['channel_id'] not in channels:
                channels[m['channel_id']] = []

            channels[m['channel_id']].append(m['user_id'])

        for channel, users in channels.items():
            c = self.bot.get_channel(channel)
            if c is None:
                continue

            index = 0
            while index < len(users):
                targets = users[index:index+4]
                index += 4
                msg = f"Hey, it's {offset} until Advent Of Code day {tz.get().day+1}!\n{''.join([f'<@!{x}>' for x in targets])}"
                try:
                    await c.send(msg, allowed_mentions=discord.AllowedMentions(users=True))
                except:
                    raise
                    break

    @commands.group(aliases=["remindme", "reminder"], invoke_without_command=True)
    @commands.guild_only()
    async def remind(self, ctx):
        async with self.bot.db.acquire() as conn:
            trans = conn.transaction()
            await trans.start()
            try:
                await ctx.send(f"Alright {ctx.author.name}, i'll remind you in this channel 10 minutes before advent of code "
                               f"challenges are released. Use `{await commands.clean_content().convert(ctx, ctx.prefix)}remind cancel` "
                               f"to stop these reminders")
                await self.bot.db.execute("INSERT INTO reminders VALUES ($1, $2)", ctx.channel.id, ctx.author.id)
            except:
                await trans.rollback()
            else:
                await trans.commit()

    @remind.command()
    @commands.guild_only()
    async def cancel(self, ctx):
        data = await self.bot.db.fetchrow("DELETE FROM reminders WHERE user_id = $1 AND channel_id = $2 RETURNING *", ctx.author.id, ctx.channel.id)
        if not data:
            return await ctx.send("Hmm, you dont seem to have a reminder in this channel")