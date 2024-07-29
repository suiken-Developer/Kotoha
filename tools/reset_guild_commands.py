# 特定ギルドのコマンドをリセットするプログラム
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv # python-dotenv


load_dotenv() # .env読み込み

TOKEN = os.getenv("TOKEN")
DEV_GUILD = int(os.getenv("DEV_GUILD"))

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


@bot.event
async def on_ready():
    guild = discord.Object(id=os.getenv("DEV_GUILD"))
    bot.tree.clear_commands(guild=guild)
    await bot.tree.sync(guild=guild)
    print(f"[Akane] Commands for {DEV_GUILD} cleared")
    game = discord.Game("メンテナンス中 | Under maintenance")
    await bot.change_presence(status=discord.Status.idle, activity=game)


bot.run(os.getenv("TOKEN"))
