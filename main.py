# 組み込みライブラリ
import asyncio
import datetime
import os
from itertools import cycle
import random

# 外部ライブラリ
import discord
from discord.ext import commands  # Bot Commands Framework
from discord.ext import tasks
from dotenv import load_dotenv  # python-dotenv


load_dotenv()  # .env読み込み

##################################################

''' 定数群 '''

TOKEN = os.getenv("TOKEN")  # Token

STARTUP_LOG = int(os.getenv("STARTUP_LOG"))
DEV_GUILD = int(os.getenv("DEV_GUILD"))
PREFIX = os.getenv("PREFIX")  # Default Prefix
VERSION = os.getenv("VERSION")

##################################################

bot = commands.Bot(command_prefix=PREFIX, intents=discord.Intents.all())


# 起動通知
@bot.event
async def on_ready():
    global bot_guilds, bot_members

    print("[Akane] ログインしました")
    bot_guilds = len(bot.guilds)
    bot_members = []

    for guild in bot.guilds:
        for member in guild.members:
            if member.bot:
                pass

            else:
                bot_members.append(member)

    activity = discord.CustomActivity(name="✅ 起動完了")
    await bot.change_presence(activity=activity)
    change_activity.start()

    # 起動メッセージを専用サーバーに送信（チャンネルが存在しない場合、スルー）
    try:
        ready_log = await bot.fetch_channel(STARTUP_LOG)
        embed = discord.Embed(title="Akane 起動完了",
                              description=f"**Akane#0940** が起動しました。"
                              f"\n```サーバー数: {bot_guilds}\n"
                              f"ユーザー数: {len(bot_members)}```",
                              timestamp=datetime.datetime.now())
        embed.set_footer(text=f"Akane - Ver{VERSION}")
        await ready_log.send(embed=embed)

    except Exception:
        pass


# Activity自動変更
@tasks.loop(seconds=10)
async def change_activity():
    global bot_guilds, bot_members

    STATUS_LIST = cycle(["❓/help", f"{bot_guilds} Servers", f"{len(bot_members)} Users", f"Version {VERSION}"])
    activity = discord.CustomActivity(name=next(STATUS_LIST))
    await bot.change_presence(activity=activity)


##################################################

''' 管理者用コマンド '''


# devhelp
@bot.command(name="devhelp")
@commands.is_owner()
async def devhelp(ctx):
    desc = "```Akane 管理者用コマンドリスト```\n**管理コマンド**\n`sync`, `devsync`"
    embed = discord.Embed(title="📖コマンドリスト", description=desc)
    await ctx.reply(embed=embed, mention_author=False)


# sync
@bot.command(name="sync")
@commands.is_owner()
async def sync(ctx):
    try:
        synced = await bot.tree.sync()

    except Exception as e:
        embed = discord.Embed(title=":x: エラー",
                              description="コマンドのSyncに失敗しました",
                              color=0xff0000)
        embed.add_field(name="エラー内容", value=e)
        await ctx.reply(embed=embed, mention_author=False)

    else:
        embed = discord.Embed(title=":white_check_mark: 成功",
                              description=f"{len(synced)}コマンドをSyncしました",
                              color=discord.Colour.green())
        await ctx.reply(embed=embed, mention_author=False)


# devsync
@bot.command(name="devsync")
@commands.is_owner()
async def sync(ctx):
    try:
        synced = await bot.tree.sync(guild=discord.Object(DEV_GUILD))

    except Exception as e:
        embed = discord.Embed(title=":x: エラー",
                              description="コマンドのSyncに失敗しました",
                              color=0xff0000)
        embed.add_field(name="エラー内容", value=e)
        await ctx.reply(embed=embed, mention_author=False)

    else:
        embed = discord.Embed(title=":white_check_mark: 成功",
                              description=f"{len(synced)}コマンドをSyncしました",
                              color=discord.Colour.green())
        await ctx.reply(embed=embed, mention_author=False)


# stop
@bot.command(name="stop")
@commands.is_owner()
async def stop(ctx):
    print("[Akane] Shutdown is requested by owner")
    embed = discord.Embed(title=":white_check_mark: 成功",
                          description="Botを停止しています",
                          color=discord.Colour.green())
    await ctx.reply(embed=embed, mention_author=False)
    await bot.close()


##################################################


# 全てのインタラクションを取得
@bot.event
async def on_interaction(ctx: discord.Interaction):
    try:
        if ctx.data['component_type'] == 2:
            await on_button_click(ctx)

        # elif inter.data['component_type'] == 3:
        #     await on_dropdown(inter)

    except KeyError:
        pass


# Buttonの処理
async def on_button_click(ctx: discord.Interaction):
    custom_id = ctx.data["custom_id"]

    if custom_id == "j_g":
        result = random.choice(range(1, 3))

        if result == 1:
            await ctx.response.send_message(f"ぽん:v: {ctx.user.mention}\n君の勝ちやで～")

        elif result == 2:
            await ctx.response.send_message(f"ぽん✊ {ctx.user.mention}\nあいこやな。")

        else:
            await ctx.response.send_message(f"ぽん✋ {ctx.user.mention}\n私の勝ちやな。また挑戦してや。")

    if custom_id == "j_c":
        result = random.choice(range(1, 3))

        if result == 1:
            await ctx.response.send_message(f"ぽん✋ {ctx.user.mention}\n君の勝ちやで～")

        elif result == 2:
            await ctx.response.send_message(f"ぽん:v: {ctx.user.mention}\nあいこやな。")

        else:
            await ctx.response.send_message(f"ぽん✊ {ctx.user.mention}\n私の勝ちやな。また挑戦してや。")

    if custom_id == "j_p":
        result = random.choice(range(1, 3))

        if result == 1:
            await ctx.response.send_message(f"ぽん✊ {ctx.user.mention}\n君の勝ちやで～")

        elif result == 2:
            await ctx.response.send_message(f"ぽん✋ {ctx.user.mention}\nあいこやな。")

        else:
            await ctx.response.send_message(f"ぽん:v: {ctx.user.mention}\n私の勝ちやな。また挑戦してや。")


##################################################

# 読み込むCogのリスト
INITIAL_EXTENSIONS = [
    'cogs.system',
    'cogs.fun',
    'cogs.shikanoko',
    'cogs.scratch',
    'cogs.user',
    'cogs.youtube',
    'cogs.guild',
    'cogs.delete',
    'cogs.nijigen',
    'cogs.useful',
    'cogs.web',
    'cogs.akane-talks',
    'cogs.akane-ai'
]


# cog読み込み
async def load_extension():
    for cog in INITIAL_EXTENSIONS:
        await bot.load_extension(cog)


# 起動
async def main():
    async with bot:
        await load_extension()
        print("[Akane] Cogを全て読み込みました")
        await bot.start(TOKEN)


# エラー処理
@bot.event
async def on_command_error(ctx: commands.Context, error):
    # Botが起こしたエラーの場合
    if ctx.author.bot:
        print(error)
    
    if isinstance(error, commands.errors.CheckFailure):  # スラッシュコマンドでのみ動作するように制約
        await ctx.send(f':x: 権限がありません', ephemeral = True)  # 権限を持たずにコマンドを実行した際に警告する


asyncio.run(main())