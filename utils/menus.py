import discord
from discord.ext import menus


class LeaderboardDataSource(menus.ListPageSource):
    def __init__(self, data, board):
        super(LeaderboardDataSource, self).__init__(data, per_page=1)
        self.board = board

    async def format_page(self, menu, page):
        return discord.Embed(description="```\n" + "".join(page) + "\n```", title=f"{self.board.owner.name}'s Leaderboard")


class InfoDataSource(menus.ListPageSource):
    def __init__(self, data):
        super(InfoDataSource, self).__init__(data, per_page=1)

    async def format_page(self, menu, page):
        return "```\n" + "".join(page) + "\n```"
