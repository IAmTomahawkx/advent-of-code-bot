import discord
from discord.ext import commands, menus

helpdict = {
  1: discord.Embed(
     title='AdventOfCode help',
     description='''
          Key: <arg> - required argument, [arg] - optional argument
          Leaderboard:
          `aoc.iam`         associates your discord user with your advent of code user.
          `aoc.info`        gives you advent of code info on the given person. if no target...
          `aoc.lang`        tells the bot that youve completed todays challenge in the give...
          `aoc.leaderboard` shows the top 5 users on your server's leaderboard
          ''',
          colour=0x2F3136
   ),
   2: discord.Embed(
     title='AdventOfCode help',
     description='''
          Key: <arg> - required argument, [arg] - optional argument
          Reminder:
          `aoc.remind` Remind you abount advent of code
          ''',
          colour=0x2F3136
   ),
   3: discord.Embed(
     title='AdventOfCode help',
     description='''
          Key: <arg> - required argument, [arg] - optional argument
          Other:
          `aoc.about`       Send info about the bot   
          `aoc.help`        Shows this message
          `aoc.invite`      gives you a link to invite this bot
          ''',
          colour=0x2F3136
   ),
}

class HelpMenu(menus.Menu):
    async def update(self, payload):
        if self._can_remove_reactions:
            if payload.event_type == 'REACTION_ADD':
                await self.bot.http.remove_reaction(
                    payload.channel_id, payload.message_id,
                    discord.Message._emoji_reaction(payload.emoji), payload.member.id
                )
            elif payload.event_type == 'REACTION_REMOVE':
                return
        await super().update(payload)

    async def send_initial_message(self, ctx, channel):
        global counter
        counter = 1
        return await channel.send(embed=helpdict[counter].set_footer(text=f'Page {counter}/3'))

    @menus.button('\U000025c0\U0000fe0f')
    async def on_back_page(self, payload):
        global counter
        counter -= 1
        if counter <= 0:
            counter = 3
        await self.message.edit(embed=helpdict[counter].set_footer(text=f'Page {counter}/3'))
        user = await self.bot.get_guild(payload.guild_id).fetch_member(payload.user_id)
        try:
            await self.message.remove_reaction(payload.emoji, user)
        except:
            pass

    @menus.button('\U000025b6\U0000fe0f')
    async def on_next_page(self, payload):
        global counter
        counter += 1
        if counter > 3:
            counter = 1
        await self.message.edit(embed=thelpdict[counter].set_footer(text=f'Page {counter}/3'))
        user = await self.bot.get_guild(payload.guild_id).fetch_member(payload.user_id)
        try:
            await self.message.remove_reaction(payload.emoji, user)
        except:
            pass


    @menus.button('\U000023f9\U0000fe0f')
    async def on_stop(self, payload):
        self.stop()
        user = await self.bot.get_guild(payload.guild_id).fetch_member(payload.user_id)
        await self.message.remove_reaction(payload.emoji, user)

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        menu = HelpMenu()
        await menu.start(ctx)

def setup(bot):
    bot.add_cog(Help(bot))
