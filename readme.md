Advent of code discord bot
==
This bot is useless for 11/12 months of the year. But it can prove quite handy for that one month.
The advent of code season.

This bot can be used as a shortcut to your leaderboard, and adds a few features to it, such as language tracking,
for people who do advent of code in more than one language.
It can also remind you a few minutes before each puzzle releases, so that you dont waste time opening your workspace,
or forget about it entirely.

Requirements
--
- Python 3.7 or 3.8
- Postgresql 11+

make sure you install the requirements (`pip install -r requirements.txt`)

To access your leaderboard, you need to give the bot your cookie. Once it is up and running, run the `cookie` command
and dm the bot your advent of code cookie. Your cookie can be found by opening the dev tools on your browser, opening
a private leaderboard, and getting the `cookie` header from the request.