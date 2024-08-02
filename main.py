# インポート群
from __future__ import unicode_literals
import discord  # discord.py
from discord.ui import Select, View
import discord.app_commands
import os
import random
import datetime
import asyncio  # タイマー
import aiohttp
import json
import requests  # zip用
import re

from yt_dlp import YoutubeDL
from dotenv import load_dotenv  # python-dotenv
import google.generativeai as genai  # google-generativeai
import urllib.parse
from aiodanbooru.api import DanbooruAPI  # aiodanbooru
import scratchattach as scratch3  # scratchattach
import qrcode  # qrcode

from pagination import Pagination  # pagination.py
from shika import shika  # shikanoko.py

##################################################
''' 初期設定 '''
load_dotenv()  # .env読み込み

# 変数群
TOKEN = os.getenv("TOKEN")  # Token
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # Gemini API Key

UR7_USERNAME = os.getenv("UR7_USERNAME")  # ur7.cc
UR7_PASSWORD = os.getenv("UR7_PASSWORD")  # ur7.cc

OWNER = int(os.getenv("OWNER"))
STARTUP_LOG = int(os.getenv("STARTUP_LOG"))
ERROR_LOG = int(os.getenv("ERROR_LOG"))
PREFIX = "k."  # Default Prefix
VERSION = "4.14.1"

# Gemini
AIMODEL_NAME = "gemini-1.5-pro-latest"

text_generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 512,
}

image_generation_config = {
    "temperature": 0.4,
    "top_p": 1,
    "top_k": 32,
    "max_output_tokens": 512,
}

safety_settings = [
    {
        "category": "HARM_CATEGORY_DANGEROUS",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
    },
]

# Prompts (一般化する予定)
with open("data/prompts/akane.txt", encoding="UTF-8") as f:
    AKANE_PROMPT = f.read()

with open("data/prompts/aoi.txt", encoding="UTF-8") as f:
    AOI_PROMPT = f.read()

with open("data/prompts/jinrou.txt", encoding="UTF-8") as f:
    JINROU_PROMPT = f.read()

with open("data/prompts/quiz.txt", encoding="UTF-8") as f:
    QUIZ_PROMPT = f.read()

SYSTEM_PROMPTS = [AKANE_PROMPT, AOI_PROMPT, JINROU_PROMPT]
CHARAS = ["琴葉茜", "琴葉葵", "人狼（β版）"]

##################################################

''' 初期処理'''

genai.configure(api_key=GOOGLE_API_KEY)

quiz_model = genai.GenerativeModel(model_name=AIMODEL_NAME,
                                   safety_settings=safety_settings,
                                   generation_config=text_generation_config,
                                   system_instruction=QUIZ_PROMPT)

# メンバーインテント
intents = discord.Intents.all()
intents.members = True

# 接続に必要なオブジェクトを生成
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

##################################################

''' 関数群 '''


def gpt(text, flag, attachment, chara):
    global AIMODEL_NAME
    '''
    Gemini本体処理

    Parameters:
    ----------
    text : str
        入力
    flag : int
        0: text, 1: image
    attachment : all
        flag = 0: history(list), flag = 1: image(image)
    chara : int
        キャラクター

    Returns:
    ----------
    image
        完成した画像
    '''
    # テキストモード
    if flag == 0:
        # キャラ数が合っていないエラー対策
        if chara > len(SYSTEM_PROMPTS) - 1:
            chara = 0

        text_model = genai.GenerativeModel(model_name=AIMODEL_NAME,
                                           safety_settings=safety_settings,
                                           generation_config=text_generation_config,
                                           system_instruction=SYSTEM_PROMPTS[int(chara)])
        chat = text_model.start_chat(history=attachment)

        # Geminiにメッセージを投げて返答を待つ。エラーはエラーとして返す。
        try:
            response = chat.send_message(text)

        except Exception as e:
            return [False, e]

        else:
            return [True, response.text]

    # 画像モード
    else:
        # エラー対策
        if chara > len(SYSTEM_PROMPTS) - 1:
            chara = 0

        image_model = genai.GenerativeModel(model_name=AIMODEL_NAME,
                                            safety_settings=safety_settings,
                                            generation_config=image_generation_config,
                                            system_instruction=SYSTEM_PROMPTS[int(chara)])
        image_parts = [{"mime_type": "image/jpeg", "data": attachment}]
        prompt_parts = [image_parts[0], f"\n{text if text else 'この画像は何ですか？'}"]

        # Geminiに画像を投げて返答を待つ。エラーはエラーとして返す。
        try:
            response = image_model.generate_content(prompt_parts)

        except Exception as e:
            return [False, e]

        else:
            return [True, response.text]


def quiz(text):
    global quiz_model

    chat = quiz_model.start_chat(history=[])
    response = chat.send_message(f"ジャンルは「{text}」でクイズを生成してください。")

    return response.text


# Akane AI用
class SelectView(View):
    def __init__(self, *, timeout: int = 60):
        super().__init__(timeout=timeout)

        async def on_timeout(self, select: Select) -> None:
            select.disabled = True

    @discord.ui.select(
        cls=Select,
        placeholder="選択してください",
        disabled=False,
        options=[
            discord.SelectOption(label="琴葉茜", value="0", description="合成音声キャラクター"),
            discord.SelectOption(label="琴葉葵", value="1", description="合成音声キャラクター"),
            discord.SelectOption(label="人狼（β版）", value="2", description="人狼ゲーム"),
        ],
    )
    async def selectMenu(self, ctx: discord.Interaction, select: Select):
        select.disabled = True

        with open(f"data/ai/{ctx.user.id}.json", "r", encoding='UTF-8') as f:
            ai_data = json.load(f)

        with open(f"data/ai/{ctx.user.id}.json", 'w', encoding='UTF-8') as f:
            json.dump([ai_data[0], int(select.values[0])], f)

        await ctx.response.edit_message(view=self)
        await ctx.followup.send(f"✅ {ctx.user.mention} のキャラクターを**{CHARAS[int(select.values[0])]}**に変更しました")


##################################################

# 起動時に動作する処理
@client.event
async def on_ready():
    global fxblocked

    # 起動したらターミナルにログイン通知が表示される
    print('[Akane] ログインしました')
    bot_guilds = len(client.guilds)
    bot_members = []

    for guild in client.guilds:
        for member in guild.members:
            if member.bot:
                pass

            else:
                bot_members.append(member)

    activity = discord.CustomActivity(name="✅ 起動完了")
    await client.change_presence(activity=activity)

    # fxtwitter
    with open("data/fxtwitter.txt") as f:
        fxblocked = f.read().split('\n')

    # 起動メッセージを専用サーバーに送信（チャンネルが存在しない場合、スルー）
    try:
        ready_log = client.get_channel(STARTUP_LOG)
        embed = discord.Embed(title="Akane 起動完了",
                              description=f"**Akane#0940** が起動しました。"
                              f"\n```サーバー数: {bot_guilds}\n"
                              f"ユーザー数: {len(bot_members)}```",
                              timestamp=datetime.datetime.now())
        embed.set_footer(text=f"Akane - Ver{VERSION}")
        await ready_log.send(embed=embed)

    except Exception:
        pass

    activity_count = 0
    activity_list = ["❓/help", f"{bot_guilds} Servers", f"{len(bot_members)} Users"]

    while True:
        await asyncio.sleep(10)

        try:
            activity = discord.CustomActivity(name=activity_list[activity_count])
            await client.change_presence(activity=activity)

        except Exception:
            pass

        if activity_count == len(activity_list) - 1:
            activity_count = 0

        else:
            activity_count = activity_count + 1


# ヘルプ
@tree.command(name="help", description="Akaneのコマンド一覧を表示します")
@discord.app_commands.describe(command="指定したコマンドの説明を表示します")
async def help(ctx: discord.Interaction, command: str = None):

    with open("data/commands.json", encoding="UTF-8") as f:
        commands = json.load(f)

    # 長さを整形したコマンド一覧
    commands_just = [cmd.ljust(12) for cmd in commands]

    commands_formatted = [f"`/{commands_just[i]}` {commands[cmd]['info']}" for (i, cmd) in zip(range(len(commands)), commands)]
    L = 10

    # 引数あり: コマンド説明
    if command:
        if commands[command]:
            category = commands[command]["category"]
            help_usage = commands[command]["usage"]
            help_info = commands[command]["info"]
            embed = discord.Embed(title=f"{category}: **{command}**", description="")
            embed.add_field(name="使い方",
                            value=f"\n```/{help_usage}```", inline=False)
            embed.add_field(name="説明",
                            value=f"```{help_info}```", inline=False)
            embed.set_footer(text="<> : 必要引数 | [] : オプション引数")
            await ctx.response.send_message(embed=embed, ephemeral=True)

        else:
            await ctx.response.send_message(":x: そのコマンドは存在しません", ephemeral=True)

    else:
        async def get_page(page: int):
            embed = discord.Embed(
                title=f"Akane (v{VERSION}) コマンドリスト",
                description="❓コマンドの詳細説明: /help <コマンド名>\n\n**コマンド**\n",
                color=discord.Colour.red())
            offset = (page - 1) * L

            for command in commands_formatted[offset:offset+L]:
                embed.description += f"{command}\n"

            n = Pagination.compute_total_pages(len(commands_formatted), L)
            embed.set_footer(text=f"ページ {page} / {n}")
            return embed, n

        await Pagination(ctx, get_page).navegate()


# cat
@tree.command(name="cat", description="ﾈｺﾁｬﾝ")
async def cat(ctx: discord.Interaction):
    nekos = ["🐱( '-' 🐱 )ﾈｺﾁｬﾝ", "ﾆｬﾝฅ(>ω< )ฅﾆｬﾝ♪",
             "ฅ•ω•ฅﾆｬﾆｬｰﾝ✧", "ฅ( ̳• ·̫ • ̳ฅ)にゃあ",
             "ﾆｬｯ(ฅ•ω•ฅ)", "ฅ•ω•ฅにぁ？",
             "( ฅ•ω•)ฅ ﾆｬｰ!", "ฅ(´ω` ฅ)ﾆｬｰ",
             "(/・ω・)/にゃー!",
             "ฅ(*´ω｀*ฅ)ﾆｬｰ", "ฅ^•ω•^ฅﾆｬｰ",
             "(/ ･ω･)/にゃー", "└('ω')┘ﾆｬｱｱｱｱｱｱｱｱｱｱ!!!!",
             "(/・ω・)/にゃー！", "ฅ•ω•ฅﾆｬｰ",
             "壁]ωФ)ﾆｬｰ", "ฅ(=･ω･=)ฅﾆｬｰ",
             "(*ΦωΦ)ﾆｬｰ", "にゃーヽ(•̀ω•́ )ゝ✧",
             "ฅ•ω•ฅﾆｬｰ♥♡", "ﾆｬｰ(/｡>ω< )/",
             "(」・ω・)」うー！(／・ω・)／にゃー！",
             "ฅฅ*)ｲﾅｲｲﾅｲ･･･ ฅ(^ •ω•*^ฅ♡ﾆｬｰ",
             "ﾆｬｰ(´ฅ•ω•ฅ｀)ﾆｬｰ", "ฅ(･ω･ฅ)ﾝﾆｬｰ♡",
             "ﾆｬｰ(ฅ *`꒳´ * )ฅ", "ฅ(^ •ω•*^ฅ♡ﾆｬｰ",
             "๑•̀ㅁ•́ฅ✧にゃ!!", "ﾆｬｯ(ฅ•ω•ฅ)♡",
             "ฅ^•ﻌ•^ฅﾆｬｰ", "ฅ( *`꒳´ * ฅ)ﾆｬｰ",
             "ฅ(๑•̀ω•́๑)ฅﾆｬﾝﾆｬﾝ!", "ฅ(・ω・)ฅにゃー💛",
             "ฅ(○•ω•○)ฅﾆｬ～ﾝ♡", "Σฅ(´ω｀；ฅ)ﾆｬｰ!?",
             "ฅ(*´ω｀*ฅ)ﾆｬｰ", "ﾆｬ-( ฅ•ω•)( •ω•ฅ)ﾆｬｰ",
             "ฅ(^ •ω•*^ฅ♡ﾆｬｰ", "ฅ•ω•ฅﾆｬﾆｬｰﾝ✧ｼｬｰ ฅ(`ꈊ´ฅ)",
             "ﾆｬﾝฅ(>ω< )ฅﾆｬﾝ♪", "ฅ( ̳• ·̫ • ̳ฅ)にゃあ",
             "ฅ(*°ω°*ฅ)*ﾆｬｰｵ", "ฅ•ω•ฅにぁ？", "♪(ฅ•∀•)ฅ ﾆｬﾝ",
             "ฅ(◍ •̀ω• ́◍)ฅﾆｬﾝﾆｬﾝがお➰🌟", "=͟͟͞͞(๑•̀ㅁ•́ฅ✧ﾆｬｯ",
             "ฅ(=✧ω✧=)ฅﾆｬﾆｬｰﾝ✧", "ﾆｬｰ(ฅ *`꒳´ * )ฅฅ( *`꒳´ * ฅ)ﾆｬｰ",
             "ฅ(๑•̀ω•́๑)ฅﾆｬﾝﾆｬﾝｶﾞｵｰ★", "_(　　_ΦДΦ)_ ﾆ\"ｬｧ\"ｧ\"ｧ\"",
             "ฅ(>ω<ฅ)ﾆｬﾝ♪☆*。", "ฅ(○•ω•○)ฅﾆｬ～ﾝ❣", "ฅ(°͈ꈊ°͈ฅ)ﾆｬｰ",
             "(ฅ✧ω✧ฅ)ﾆｬ", "(ฅฅ)にゃ♡", "ฅ^•ﻌ•^ฅﾆｬﾝ",
             "ヾ(⌒(_´,,−﹃−,,`)_ゴロにゃん",
             "ฅ•ω•ฅﾆｬﾆｬｰﾝ✧", "๑•̀ㅁ•́ฅ✧にゃ!!",
             "ヾ(⌒(_*Φ ﻌ Φ*)_ﾆｬｰﾝ♡",
             "ᗦ↞◃ ᗦ↞◃ ᗦ↞◃ ᗦ↞◃ ฅ(^ω^ฅ) ﾆｬ～"]
    await ctx.response.send_message(random.choice(nekos))


# 招待リンク
@tree.command(name="invite", description="Akaneの招待リンクを表示するで")
async def invite(ctx: discord.Interaction):
    button = discord.ui.Button(label="招待する", style=discord.ButtonStyle.link,
                               url="https://discord.com/oauth2/authorize?client_id=777557090562474044")
    embed = discord.Embed(title="招待リンク",
                          description="下のボタンからAkaneを招待できるで！（サーバー管理権限が必要です)",
                          color=0xdda0dd)
    view = discord.ui.View()
    view.add_item(button)
    await ctx.response.send_message(embed=embed, view=view, ephemeral=True)


# じゃんけん
@tree.command(name="janken", description="じゃんけん")
async def janken(ctx: discord.Interaction):
    button1 = discord.ui.Button(label="ぐー", style=discord.ButtonStyle.primary, custom_id="j_g")
    button2 = discord.ui.Button(label="ちょき", style=discord.ButtonStyle.success, custom_id="j_c")
    button3 = discord.ui.Button(label="ぱー", style=discord.ButtonStyle.danger, custom_id="j_p")
    view = discord.ui.View()
    view.add_item(button1)
    view.add_item(button2)
    view.add_item(button3)
    await ctx.response.send_message("最初はぐー、じゃんけん", view=view)


# dice
@tree.command(name="dice", description="サイコロを振るで")
@discord.app_commands.describe(pcs="サイコロの個数（1~100）")
@discord.app_commands.describe(maximum="サイコロの最大値（1～999）")
async def dice(ctx: discord.Interaction, pcs: int = 1, maximum: int = 6):
    # エラー: サイコロの個数が範囲外
    if not 0 < pcs < 101:
        embed = discord.Embed(title=":x: エラー",
                              description="サイコロの個数は1~100で指定してください",
                              color=0xff0000)
        await ctx.response.send_message(embed=embed, ephemeral=True)

    # エラー: サイコロの目が範囲外
    elif not 0 < maximum < 1000:
        embed = discord.Embed(title=":x: エラー",
                              description="サイコロの目の最大値は個数は1~999で指定してください",
                              color=0xff0000)
        await ctx.response.send_message(embed=embed, ephemeral=True)

    else:
        # maximumが6以下なら絵文字を使用する
        if maximum > 6:
            dices = [random.randint(1, maximum) for i in range(pcs)]

        else:
            word_list = [":one:", ":two:", ":three:",
                         ":four:", ":five:", ":six:"]
            word_list = word_list[:(maximum - 1)]
            dices = [random.choice(word_list) for i in range(pcs)]

        await ctx.response.send_message(
            f":game_die: {', '.join(map(str, dices))}が出たで")


# ping
@tree.command(name="ping", description="AkaneのPingを確認するで")
async def ping(ctx: discord.Interaction):
    embed = discord.Embed(title="Pong!",
                          description=f"`{round(client.latency * 1000, 2)}ms`",
                          color=0xc8ff00)
    await ctx.response.send_message(embed=embed)


# kuji
@tree.command(name="kuji", description="おみくじ")
@discord.app_commands.describe(pcs="引く枚数（1~100）")
async def kuji(ctx: discord.Interaction, pcs: int = 1):
    # エラー: 枚数が範囲外
    if not 0 < pcs < 101:
        embed = discord.Embed(title=":x: エラー",
                              description="引くおみくじの枚数は1~100で指定してください",
                              color=0xff0000)
        await ctx.response.send_message(embed=embed, ephemeral=True)

    else:
        omikuji_list = ["大大凶", "大凶", "凶", "末吉",
                        "小吉", "中吉", "吉", "大吉", "大大吉"]
        kuji_results = [""] * pcs
        points = 0

        if pcs > 1:
            for i in range(pcs):
                j = random.choice(omikuji_list)
                points += omikuji_list.index(j) + 1
                kuji_results[i] = f"**{j}**"

            await ctx.response.send_message(f"今日の運勢は... {', '.join(map(str, kuji_results))}！"
                                            f"（{pcs}連おみくじ総合運勢: **{omikuji_list[(points // pcs) - 1]}）**")

        else:
            await ctx.response.send_message(f"今日の運勢は... **{random.choice(omikuji_list)}**！")


# shikanoko
@tree.command(name="shikanoko", description="「しかのこのこのここしたんたん」を引き当てよう")
@discord.app_commands.describe(pcs="回数（1~10）")
async def shikanoko(ctx: discord.Interaction, pcs: int = 1):
    # エラー: 枚数が範囲外
    if not 0 < pcs < 11:
        embed = discord.Embed(title=":x: エラー",
                              description="回数は1~10で指定してください",
                              color=0xff0000)
        await ctx.response.send_message(embed=embed, ephemeral=True)

    else:
        if pcs > 1:
            results = ""

            for i in range(pcs):
                c = "し"
                words = [c]

                while True:
                    c = shika(c)

                    if c == "END":
                        word = "".join(words)
                        results += f"・{word}\n"
                        break

                    else:
                        words.append(c)

            if "しかのこのこのここしたんたん" in results:
                status = "あたり！"

            else:
                status = "はずれ！"

            embed = discord.Embed(title=":deer: しかのこのこのここしたんたん",
                                  description=f"{results}\n\n**{status}**",
                                  color=discord.Colour.green())
            await ctx.response.send_message(embed=embed)

        else:
            c = "し"
            words = [c]

            while True:
                c = shika(c)

                if c == "END":
                    word = "".join(words)
                    break

                else:
                    words.append(c)

            if word == "しかのこのこのここしたんたん":
                status = "あたり！"

            else:
                status = "はずれ！"

            embed = discord.Embed(title=":deer: しかのこのこのここしたんたん",
                                  description=f"{word}\n\n**{status}**",
                                  color=discord.Colour.green())
            await ctx.response.send_message(embed=embed)


# userinfo
@tree.command(name="userinfo", description="ユーザー情報を取得するで")
@discord.app_commands.describe(user="ユーザーをメンションまたはユーザーIDで指定")
async def userinfo(ctx: discord.Interaction, user: str):
    # メンションからID抽出
    target = re.sub("\\D", "", str(user))

    # ユーザーIDからユーザーを取得
    try:
        user = await client.fetch_user(target)

    # できなかったらエラー出す
    except Exception:
        embed = discord.Embed(title=":x: エラー",
                              description="そのユーザーを取得できませんでした",
                              color=0xff0000)
        await ctx.response.send_message(embed=embed, ephemeral=True)

    else:
        embed = discord.Embed(title="ID",
                              description=target,
                              color=discord.Colour.green())
        try:
            embed.set_author(name=user, icon_url=user.avatar_url)
            embed.set_thumbnail(url=user.avatar_url)

        except Exception:
            pass

        if str(user.discriminator) == "0":
            embed.add_field(name="アカウント名", value=user.name, inline=True)

        else:
            embed.add_field(name="アカウント名", value=f"{user.name}#{user.discriminator}", inline=True)
            # embed.add_field(name="ステータス", value=user.status,inline=True)
            embed.add_field(name="メンション", value=user.mention, inline=True)
            embed.set_footer(text=f"アカウント作成日時: {user.created_at}")

        if hasattr(user.avatar, 'key'):
            embed.set_thumbnail(url=user.avatar.url)

        await ctx.response.send_message(embed=embed)


# scinfo
@tree.command(name="scinfo", description="Scratchのユーザー情報を取得します")
@discord.app_commands.describe(user="ユーザー名")
async def scinfo(ctx: discord.Interaction, user: str):
    await ctx.response.defer()

    try:
        user = scratch3.get_user(user)

    except Exception:
        embed = discord.Embed(title=":x: エラー",
                              description="そのユーザーを取得できませんでした",
                              color=0xff0000)
        await ctx.followup.send(embed=embed, ephemeral=True)

    else:
        if user.scratchteam:
            embed = discord.Embed(
                title="ユーザー名",
                description=f"[{user}](https://scratch.mit.edu/users/{user}) [Scratchチーム]",
                color=discord.Colour.green())
        else:
            embed = discord.Embed(
                title="ユーザー名",
                description=f"[{user}](https://scratch.mit.edu/users/{user})",
                color=discord.Colour.green())

        try:
            embed.set_thumbnail(url=user.icon_url)

        except Exception:
            pass

        jd = user.join_date

        embed.add_field(name="ユーザーID",
                        value=user.id, inline=True)
        embed.add_field(name="国",
                        value=user.country, inline=True)
        embed.add_field(name="通知数",
                        value=user.message_count(), inline=True)
        embed.add_field(name="フォロー数",
                        value=user.following_count(), inline=True)
        embed.add_field(name="フォロワー数",
                        value=user.follower_count(), inline=True)
        embed.add_field(name="共有したプロジェクト数",
                        value=user.project_count(), inline=True)
        embed.add_field(name="お気に入りプロジェクト数",
                        value=user.favorites_count(), inline=True)
        # embed.add_field(name="フォローしているスタジオ数",
        # value=user.studio_following_count(), inline=True)
        embed.add_field(name="キュレーションしたスタジオ数",
                        value=user.studio_count(), inline=True)
        embed.add_field(name="私について",
                        value=user.about_me, inline=False)
        embed.add_field(name="私が取り組んでいること",
                        value=user.wiwo, inline=False)
        embed.set_footer(text=f"アカウント作成日時: {jd[:4]}/{jd[5:7]}/{jd[8:10]} {jd[11:19]}")

        await ctx.followup.send(embed=embed)


# scff
@tree.command(name="scff", description="Scratchの特定ユーザーがフォロー・フォロワーか確認します")
@discord.app_commands.describe(mode="モード選択")
@discord.app_commands.describe(target="対象ユーザー名")
@discord.app_commands.describe(user="フォロー・フォロワーであるか確認するユーザー名")
@discord.app_commands.choices(mode=[
    discord.app_commands.Choice(name="following", value="following"),
    discord.app_commands.Choice(name="follower", value="follower"),])
async def scff(ctx: discord.Interaction, mode: str, target: str, user: str):
    await ctx.response.defer()

    try:
        us = scratch3.get_user(target)

    except Exception:
        embed = discord.Embed(title=":x: エラー",
                              description="ユーザーを取得できませんでした",
                              color=0xff0000)
        await ctx.followup.send(embed=embed, ephemeral=True)

    else:
        if mode == "following":
            try:
                data = us.is_following(user)

            except Exception:
                embed = discord.Embed(title=":x: エラー",
                                      description="ユーザーを取得できませんでした",
                                      color=0xff0000)
                await ctx.followup.send(embed=embed, ephemeral=True)

            else:
                if data:
                    status = "しています"

                else:
                    status = "していません"

                embed = discord.Embed(title="フォロー判定",
                                      description=f"`@{target}`は`@{user}`を**フォロー{status}**",
                                      color=discord.Colour.green())
                await ctx.followup.send(embed=embed)

        if mode == "follower":
            try:
                data = us.is_followed_by(user)

            except Exception:
                embed = discord.Embed(title=":x: エラー",
                                      description="ユーザーを取得できませんでした",
                                      color=0xff0000)
                await ctx.followup.send(embed=embed, ephemeral=True)

            else:
                if data:
                    status = "されています"

                else:
                    status = "されていません"

                embed = discord.Embed(title="フォロワー判定",
                                      description=f"`@{target}`は`@{user}`に**フォロー{status}**",
                                      color=discord.Colour.green())
                await ctx.followup.send(embed=embed)


# url
@tree.command(name="url", description="URLを短縮します")
@discord.app_commands.describe(url="URLを貼り付け")
async def url(ctx: discord.Interaction, url: str):
    await ctx.response.defer()

    request = requests.post(
        "https://ur7.cc/yourls-api.php?username={UR7_USERNAME}&password={UR7_PASSWORD}&action=shorturl&format=json&url={url}"
        )

    r = request.json()

    try:
        short = json.dumps(r["shorturl"])

    except Exception:
        embed = discord.Embed(title=":x: エラー",
                              description="エラーが発生しました。",
                              color=0xff0000)
        await ctx.followup.send(embed=embed, ephemeral=True)

    else:
        embed = discord.Embed(title="短縮URL",
                              description="URLを短縮しました。\n`{0}`".format(short.strip('"')),
                              color=discord.Colour.green())
        embed.set_footer(text="Powered by UR7 Shortener")
        await ctx.followup.send(embed=embed, ephemeral=True)


# youtubedl
@tree.command(name="ytdl", description="YouTube動画のダウンロードリンクを取得します")
@discord.app_commands.describe(url="動画URLを指定")
@discord.app_commands.describe(option="オプションを指定")
@discord.app_commands.choices(option=[
    discord.app_commands.Choice(name='videoonly', value=1),
    discord.app_commands.Choice(name='soundonly', value=2),
])
async def ytdl(ctx: discord.Interaction, url: str,
               option: discord.app_commands.Choice[int] = None):
    await ctx.response.defer()

    if url.startswith("https://www.youtube.com/playlist"):
        embed = discord.Embed(title=":x: エラー",
                              description="プレイリストのダウンロードリンクは取得できません",
                              color=0xff0000)
        await ctx.followup.send(embed=embed, ephemeral=True)

    else:
        url = url.split('&')[0]

        try:
            if option.value == 1:
                youtube_dl_opts = {'format': 'bestvideo', 'max-downloads': '1'}
                opt = "動画のみ"

            elif option.value == 2:
                youtube_dl_opts = {'format': 'bestaudio[ext=m4a]', 'max-downloads': '1'}
                opt = "音声のみ"

        except Exception:
            youtube_dl_opts = {'format': 'best', 'max-downloads': '1'}
            opt = "なし"

        try:
            with YoutubeDL(youtube_dl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                video_url = info_dict.get("url", None)
                video_title = info_dict.get('title', None)

        except Exception:
            embed = discord.Embed(title=":x: エラー",
                                  description="エラーが発生しました。",
                                  color=0xff0000)
            await ctx.followup.send(embed=embed, ephemeral=True)

        else:
            embed = discord.Embed(
                title="YouTube動画ダウンロードリンク",
                description=f"`{video_title}`のダウンロードリンクを取得しました。URLは約6時間有効です。 "
                            f"(オプション: {opt})\n\n[クリックしてダウンロード]({video_url})\n"
                            f"※YouTubeによる自動生成動画はダウンロードに失敗する場合があります\n"
                            f":warning: 著作権に違反してアップロードされた動画をダウンロードすることは違法です",
                color=discord.Colour.red())
            await ctx.followup.send(embed=embed, ephemeral=True)


# unban
@tree.command(name="unban", description="ユーザーのBAN解除をします")
@discord.app_commands.default_permissions(administrator=True)
@discord.app_commands.describe(user="ユーザーをメンションまたはユーザーIDで指定")
async def unban(ctx: discord.Interaction, user: str):
    if not ctx.guild:
        embed = discord.Embed(title=":x: エラー",
                              description="このコマンドはDMで使用できません",
                              color=0xff0000)
        await ctx.response.send_message(embed=embed, ephemeral=True)

    else:
        # メンションからID抽出
        target = re.sub("\\D", "", str(user))

        try:
            user = await client.fetch_user(target)

        # できなかったらエラー出す
        except Exception:
            embed = discord.Embed(title=":x: エラー",
                                  description="そのユーザーを取得できませんでした",
                                  color=0xff0000)
            await ctx.response.send_message(embed=embed, ephemeral=True)

        else:
            try:
                await ctx.guild.unban(user)

            except Exception:
                embed = discord.Embed(title=":x: エラー",
                                      description="そのユーザーをBAN解除できません",
                                      color=0xff0000)
                await ctx.response.send_message(embed=embed, ephemeral=True)

            else:
                embed = discord.Embed(title=":white_check_mark: 成功",
                                      description="BAN解除が完了しました。\n",
                                      timestamp=datetime.datetime.now(),
                                      color=discord.Colour.green())
                try:
                    embed.set_thumbnail(url=user.avatar_url)

                except Exception:
                    pass

                # if not reason:
                #     reason = "理由がありません"
                embed.add_field(name="**BAN解除されたユーザー**",
                                value=f"{user} [ID:{target}]",
                                inline=False)
                # embed.add_field(name="**理由**",
                #                 value=f"{reason}",
                #                 inline=False))
                embed.add_field(name="**実行者**",
                                value=f"<@!{ctx.author.id}>",
                                inline=False)
                await ctx.response.send_message(embed=embed)


# delete
@tree.command(name="delete", description="10秒以上前のメッセージを削除します")
@discord.app_commands.default_permissions(administrator=True)
@discord.app_commands.describe(num="削除件数を指定 (1~100)")
async def delete(ctx: discord.Interaction, num: int):
    if not ctx.guild:
        embed = discord.Embed(title=":x: エラー",
                              description="このコマンドはDMで使用できません",
                              color=0xff0000)
        await ctx.response.send_message(embed=embed, ephemeral=True)

    elif num > 100:
        embed = discord.Embed(title=":x: エラー",
                              description="100件を超えるメッセージを削除することはできません",
                              color=0xff0000)
        await ctx.response.send_message(embed=embed, ephemeral=True)

    else:
        channel = ctx.channel
        now = datetime.datetime.now() - datetime.timedelta(seconds=10)
        await ctx.response.defer()

        try:
            deleted = await channel.purge(before=now, limit=int(num), reason=f'{ctx.user}によるコマンド実行')

        except Exception:
            embed = discord.Embed(title=":x: エラー",
                                  description="エラーが発生しました",
                                  color=0xff0000)
            await ctx.followup.send(embed=embed, ephemeral=True)

        else:
            embed = discord.Embed(title=":white_check_mark: 成功",
                                  description=f"`{len(deleted)}`件のメッセージを削除しました",
                                  color=discord.Colour.green())
            await ctx.followup.send(embed=embed, ephemeral=True)


# GuildIcon
@tree.command(name="getguildicon", description="このサーバーのアイコンを取得します")
async def getguildicon(ctx: discord.Interaction):
    # if c

    try:
        guildicon = ctx.guild.icon.replace(static_format='png')

    except Exception:
        embed = discord.Embed(title=":x: エラー",
                              description="サーバーアイコンを取得できません",
                              color=0xff0000)
        await ctx.response.send_message(embed=embed, ephemeral=True)

    else:
        embed = discord.Embed(title="サーバーアイコン",
                              description=":white_check_mark:画像を取得しました。")
        embed.set_thumbnail(url=guildicon)
        await ctx.response.send_message(embed=embed, ephemeral=True)


# danbooru
@tree.command(name="danbooru", description="Danbooruで画像検索します")
@discord.app_commands.describe(tags="タグを半角カンマ区切りで指定")
async def danbooru(ctx: discord.Interaction, tags: str = None):
    await ctx.response.defer()

    try:
        tag_list = tags.split(',')
        tag_list = [i.strip() for i in tag_list]

    except Exception:
        try:
            dan = DanbooruAPI(base_url="https://danbooru.donmai.us")
            post = await dan.get_random_post()

        except Exception:
            embed = discord.Embed(title=":x: エラー",
                                  description="検索に失敗しました。レート制限の可能性があります。",
                                  color=0xff0000)
            await ctx.followup.send(embed=embed, ephemeral=True)

        else:
            embed = discord.Embed(title="検索結果",
                                  description="オプション: ランダム検索")
            embed.set_image(url=post.media_url)
            embed.set_footer(text="Powered by Danbooru")
            await ctx.followup.send(embed=embed)

    else:
        try:
            dan = DanbooruAPI(base_url="https://danbooru.donmai.us")
            posts = await dan.get_posts(tags=tag_list, limit=200)

            post = posts[int(random.randint(0, 199))]

        except Exception:
            embed = discord.Embed(
               title=":x: エラー",
               description="検索に失敗しました。タグが正しくないか、レート制限の可能性があります。\n"
                           "利用可能はタグは以下から確認できます。\n\n"
                           "※検索のコツ※\n"
                           "・キャラクター名をローマ字、アンダーバー区切りにする（例: kotonoha_akane）\n"
                           "・作品名を正しい英語表記 or ローマ字表記にする",
               color=0xff0000)
            button = discord.ui.Button(label="ページを開く",
                                       style=discord.ButtonStyle.link,
                                       url="https://danbooru.donmai.us/tags")
            view = discord.ui.View()
            view.add_item(button)
            await ctx.followup.send(embed=embed, view=view, ephemeral=True)

        else:
            embed = discord.Embed(title="検索結果", description="オプション: なし")
            embed.set_image(url=post.media_url)
            embed.set_footer(text="Powered by Danbooru")
            await ctx.followup.send(embed=embed)


# fixtweet
@tree.command(name="fixtweet", description="このチャンネルでのツイート自動展開(fxtwitter)を有効化・無効化します")
@discord.app_commands.default_permissions(administrator=True)
async def fixtweet(ctx: discord.Interaction):
    global fxblocked

    if str(ctx.channel.id) in fxblocked:
        del fxblocked[fxblocked.index(str(ctx.channel.id))]

        with open("data/fxtwitter.txt", mode='w') as f:
            f.write('\n'.join(fxblocked))

        embed = discord.Embed(title=":white_check_mark: 成功",
                              description="このチャンネルでのツイート自動展開(fxtwitter)を**無効化**しました",
                              color=discord.Colour.green())
        await ctx.response.send_message(embed=embed, ephemeral=True)

    else:
        fxblocked.append(str(ctx.channel.id))

        with open("data/fxtwitter.txt", mode='w') as f:
            f.write('\n'.join(fxblocked))

        embed = discord.Embed(title=":white_check_mark: 成功",
                              description="このチャンネルでのツイート自動展開(fxtwitter)を**有効化**しました",
                              color=discord.Colour.green())
        await ctx.response.send_message(embed=embed, ephemeral=True)


# 5000choen
class GosenChoen(discord.ui.Modal, title='「5000兆円欲しい！」ジェネレーター'):
    line1 = discord.ui.TextInput(
        label='上の行',
        placeholder='5000兆円',
        required=True,
        max_length=50,
    )

    line2 = discord.ui.TextInput(
        label='下の行',
        placeholder='欲しい！',
        required=True,
        max_length=50,
    )

    async def on_submit(self, ctx: discord.Interaction):
        url = "https://gsapi.cbrx.io/image?top={self.line1.value}&bottom={self.line2.value}&type=png"

        try:
            embed = discord.Embed()
            embed.set_image(url=url)
            embed.set_footer(text="Powered by 5000choyen-api")
            await ctx.response.send_message(embed=embed, ephemeral=False)

        except Exception:
            embed = discord.Embed(title=":x: エラー",
                                  description="作成に失敗しました。",
                                  color=0xff0000)
            await ctx.response.send_message(embed=embed, ephemeral=True)

    async def on_error(
            self, ctx: discord.Interaction, error: Exception) -> None:
        embed = discord.Embed(title=":x: エラー",
                              description="作成に失敗しました。",
                              color=0xff0000)
        await ctx.response.send_message(embed=embed, ephemeral=True)
        # print(e)


# 5000choen
@tree.command(name="gosen", description="「5000兆円欲しい！」ジェネレーター")
async def gosen_choen(ctx: discord.Interaction):
    await ctx.response.send_modal(GosenChoen())


# QRCode
class QRCode(discord.ui.Modal, title='QRコード作成'):
    line1 = discord.ui.TextInput(
        label='QRコードにする文字列',
        placeholder='https://google.com/',
        required=True,
        max_length=500,
    )

    async def on_submit(self, ctx: discord.Interaction):
        qr_str = str(self.line1.value)

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=6
        )

        qr.add_data(qr_str)

        try:
            qr.make(fit=True)
            img = qr.make_image()
            img.save("qr.png")
            file = discord.File(fp="qr.png", filename="qr.png", spoiler=False)

        except Exception:
            embed = discord.Embed(title=":x: エラー",
                                  description="作成に失敗しました。文字列を短くするか、変更してください。",
                                  color=0xff0000)
            await ctx.response.send_message(embed=embed, ephemeral=True)

        else:
            embed = discord.Embed(title="QRコード")
            embed.set_image(url="attachment://qr.png")
            await ctx.response.send_message(
                file=file, embed=embed, ephemeral=False)

    async def on_error(
            self, ctx: discord.Interaction, error: Exception) -> None:
        embed = discord.Embed(title=":x: エラー",
                              description="作成に失敗しました。文字列を短くするか、変更してください。",
                              color=0xff0000)
        await ctx.response.send_message(embed=embed, ephemeral=True)
        print(error)


# QRCode
@tree.command(name="qr", description="QRコード作成")
async def qr(ctx: discord.Interaction):
    await ctx.response.send_modal(QRCode())


# anime
@tree.command(name="animesearch", description="画像からアニメを特定します")
@discord.app_commands.describe(image="画像をアップロード")
async def animesearch(ctx: discord.Interaction, image: discord.Attachment):
    await ctx.response.defer()

    try:
        r = requests.get("https://api.trace.moe/search?anilistInfo&"
                         f"url={urllib.parse.quote_plus(image.url)}").json()

        aninames = [entry['anilist']['title']['native'] for entry in r['result']]

        result = ""

        aninames = list(dict.fromkeys(aninames))

        for i in aninames:
            result = result + f"・{i}\n"

    except Exception:
        embed = discord.Embed(title=":x: エラー",
                              description="検索に失敗しました。画像が壊れていないことを確認したうえで、しばらく時間をおいてください。",
                              color=0xff0000)
        await ctx.followup.send(embed=embed, ephemeral=True)

    else:
        embed = discord.Embed(title="検索結果",
                              description=f"{len(aninames)}件の候補が見つかりました。\n```{result}```")
        embed.set_footer(text="Powered by Trace.moe")
        await ctx.followup.send(embed=embed)


@client.event
async def on_message(message):

    if message.author.bot or message.mention_everyone:
        return

    # オフにする機能実装するまで無効化
    #  if message.content == "せやな":
    #    #i = random.choice([0, 1])
    #
    #    await message.channel.send("<:Seyana:851104856110399488>")

    if message.guild:
        if message.channel.name == "akane-talk":
            reps = [
              "あ ほ く さ", "あほくさ", "せやな", "あれな",
              "ええで", "ええんちゃう？", "ほんま", "知らんがな",
              "知らんけど～", "それな", "そやな", "わかる", "なんや",
              "うん", "どしたん？", "やめたら？そのゲーム", "な。",
              "うん？", "わかる（感銘）", "わかる（天下無双）",
              "マ？", "Sorena...", "はよ", "Seyana...",
              "や↑ったぜ", "なに買って来たん？", "ほかには？",
              "そぉい！", "ウマいやろ？",
            ]
            i = random.choice(reps)
            await message.channel.send(i)

        elif message.channel.name == "akane-ai":
            if message.content.startswith("::") or message.content.startswith("//"):
                pass

            else:
                async with message.channel.typing():
                    # メッセージカウント
                    if message.content == f"{PREFIX}count":
                        if os.path.isfile(f"data/ai/{message.author.id}.json"):
                            with open(f"data/ai/{message.author.id}.json", "r", encoding='UTF-8') as f:
                                ai_data = json.load(f)

                            await message.reply(f"あなたの総会話回数: {ai_data[0]}回（保存中の会話履歴: 直近{min(len(ai_data) - 2, 30)}件）",
                                                mention_author=False)

                        else:
                            await message.reply("あなたの総会話回数: 0回", mention_author=False)

                        response = ""

                    # 会話履歴リセット
                    elif message.content == f"{PREFIX}clear":
                        if os.path.isfile(f"data/ai/{message.author.id}.json"):
                            with open(f"data/ai/{message.author.id}.json", "r", encoding="UTF-8") as f:
                                ai_data = json.load(f)

                            count = [int(ai_data[0]), int(ai_data[1])]

                            with open(f"data/ai/{message.author.id}.json", "w", encoding="UTF-8") as f:
                                json.dump(count, f)

                            await message.reply(":white_check_mark: 会話履歴を削除しました", mention_author=False)

                        else:
                            await message.reply(":x: まだ会話を行っていません", mention_author=False)

                        response = ""

                    # キャラクター変更
                    elif message.content == f"{PREFIX}chara":
                        if os.path.isfile(f"data/ai/{message.author.id}.json"):
                            with open(f"data/ai/{message.author.id}.json", "r", encoding="UTF-8") as f:
                                ai_data = json.load(f)

                            view = SelectView()

                            # キャラクター削除対応
                            if ai_data[1] > len(CHARAS) - 1:
                                chara_present = CHARAS[0]

                            else:
                                chara_present = CHARAS[ai_data[1]]

                            await message.reply("変更するキャラクターを選択してください\n"
                                                f"現在のキャラクター: **{chara_present}**\n\n"
                                                ":warning: キャラクターを変更すると会話履歴がリセットされます", view=view)

                        else:
                            await message.reply(":x: まだ会話を行っていません", mention_author=False)

                        response = ""

                    # 統計表示
                    elif message.content == f"{PREFIX}stats":
                        try:
                            total_talks = 0

                            # フォルダ内の全てのjsonファイルを取得してカウント
                            for file_name in os.listdir("data/ai"):
                                if file_name.endswith('.json'):
                                    file_path = os.path.join("data/ai", file_name)

                                    with open(file_path, "r", encoding="UTF-8") as file:
                                        data = json.load(file)

                                    total_talks += data[0]

                            total_users = sum(os.path.isfile(os.path.join("data/ai", name)) for name in os.listdir("data/ai")) - 1

                        except Exception:
                            await message.reply(":x: エラーが発生しました", mention_author=False)

                        else:
                            embed = discord.Embed(title="Akane AI 統計情報",
                                                  description=f"**総会話回数**\n{total_talks}回\n\n"
                                                              f"**総ユーザー数**\n{total_users}人\n\n"
                                                              f"**AIモデル**\n{AIMODEL_NAME}\n\n",
                                                  color=discord.Colour.green())
                            embed.set_footer(text=f"Akane v{VERSION}")
                            await message.reply(embed=embed, mention_author=False)

                            response = ""

                    # ヘルプ
                    elif message.content == f"{PREFIX}help":
                        embed = discord.Embed(title="Akane AIチャット ヘルプ",
                                              description="AIチャットのヘルプメニューです。",
                                              color=discord.Colour.red())
                        embed.add_field(name="機能紹介",
                                        value="・Akane AIとの会話\n"
                                              "・画像認識\n"
                                             f"・`{PREFIX}count`と送信して会話回数の表示",
                                        inline=False)
                        embed.add_field(name="注意事項",
                                        value="・AIと会話しない場合は、メッセージの先頭に`::`または`//`を付けてください。\n"
                                              "・会話履歴はAkaneと各ユーザー間で保存されます（直近30件まで）。"
                                              "他のユーザーとの会話に割り込むことはできません。\n"
                                             f"・会話に不調を感じる場合は、`{PREFIX}clear`と送信し、会話履歴をリセットしてください。\n"
                                              "・Discord規約や公序良俗に反する発言を行ったり、Akaneにそのような発言を促す行為を禁止します。",
                                        inline=False)
                        embed.add_field(name="専用コマンド",
                                        value="※以下のコマンドは`#akane-ai`チャンネル内でのみご利用いただけます。\n"
                                             f"`{'k.chara'.ljust(12)}` AIのキャラクターを変更する\n"
                                             f"`{'k.clear'.ljust(12)}` 会話履歴のリセット\n"
                                             f"`{'k.stats'.ljust(12)}` 統計情報の表示",
                                        inline=False)
                        embed.set_footer(text="不具合等連絡先: @bz6")
                        await message.reply(embed=embed, mention_author=False)
                        response = ""

                    # 画像データかどうか（画像は過去ログ使用不可）
                    elif message.attachments:
                        flag = 1

                        for attachment in message.attachments:
                            # 対応している画像形式なら処理
                            if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                                async with aiohttp.ClientSession() as session:
                                    async with session.get(attachment.url) as resp:
                                        if resp.status != 200:
                                            await message.reply(":x: 画像が読み取れません。時間を空けてから試してください。",
                                                                mention_author=False)
                                            response = ""

                                        else:
                                            image_data = await resp.read()

                                            bracket_pattern = re.compile(r'<[^>]+>')
                                            cleaned_text = \
                                                bracket_pattern.sub('', message.content)

                                            if os.path.isfile(f"data/ai/{message.author.id}.json"):
                                                with open(f"data/ai/{message.author.id}.json", "r", encoding="UTF-8") as f:
                                                    ai_data = json.load(f)

                                                chara = ai_data[1]

                                            else:
                                                chara = 0
                                                ai_data = [0, 0]

                                                with open(f"data/ai/{message.author.id}.json", "w", encoding="UTF-8") as f:
                                                    json.dump(ai_data, f)

                                                embed = discord.Embed(title="Akane AIチャット",
                                                                      description="AIチャットのご利用ありがとうございます。",
                                                                      color=discord.Colour.red())
                                                embed.add_field(name="機能紹介",
                                                                value="・Akane AIとの会話\n"
                                                                      "・画像認識\n"
                                                                     f"・`{PREFIX}count`と送信して会話回数の表示",
                                                                inline=False)
                                                embed.add_field(name="注意事項",
                                                                value="・AIと会話しない場合は、メッセージの先頭に`::`または`//`を付けてください。\n"
                                                                      "・会話履歴はAkaneと各ユーザー間で保存されます（直近30件まで）。他のユーザーとの会話に割り込むことはできません。\n"
                                                                     f"・会話に不調を感じる場合は、`{PREFIX}clear`と送信し、会話履歴をリセットしてください。\n"
                                                                      "・Discord規約や公序良俗に反する発言を行ったり、Akaneにそのような発言を促す行為を禁止します。",
                                                                inline=False)
                                                embed.add_field(name="専用コマンド",
                                                                value="※以下のコマンドは`#akane-ai`チャンネル内でのみご利用いただけます。\n"
                                                                     f"`{'k.chara'.ljust(12)}` AIのキャラクターを変更する\n"
                                                                     f"`{'k.clear'.ljust(12)}` 会話履歴のリセット\n"
                                                                     f"`{'k.stats'.ljust(12)}` 統計情報の表示",
                                                                inline=False)
                                                embed.set_footer(text="不具合等連絡先: @bz6")
                                                await message.reply(embed=embed)

                                            response = gpt(cleaned_text, 1, image_data, chara)

                            else:
                                await message.reply(":x: 画像が読み取れません。ファイルを変更してください。\n"
                                                    "対応しているファイル形式: ```.png .jpg .jpeg .gif .webp```",
                                                    mention_author=False)
                                response = ""

                    else:
                        # 過去データ読み取り
                        flag = 0

                        # 会話したことがあるか
                        if os.path.isfile(f"data/ai/{message.author.id}.json"):
                            with open(f"data/ai/{message.author.id}.json", "r", encoding='UTF-8') as f:
                                ai_data = json.load(f)

                            if len(ai_data) == 2:
                                history = []

                            elif len(ai_data) >= 32:
                                history = list(ai_data[-30:])

                            else:
                                history = list(ai_data[2:])

                            # print(history)
                            response = gpt(message.content, 0, history, ai_data[1])

                        # 会話が初めてならjson作成＆インストラクション
                        else:
                            ai_data = [0, 0]
                            history = []

                            with open(f"data/ai/{message.author.id}.json", "w", encoding="UTF-8") as f:
                                json.dump(ai_data, f)

                            embed = discord.Embed(title="Akane AIチャット",
                                                  description="AIチャットのご利用ありがとうございます。",
                                                  color=discord.Colour.red())
                            embed.add_field(name="機能紹介",
                                            value="・Akane AIとの会話\n"
                                                  "・画像認識\n"
                                                 f"・`{PREFIX}count`と送信して会話回数の表示",
                                            inline=False)
                            embed.add_field(name="注意事項",
                                            value="・AIと会話しない場合は、メッセージの先頭に`::`または`//`を付けてください。\n"
                                                  "・会話履歴はAkaneと各ユーザー間で保存されます（直近30件まで）。他のユーザーとの会話に割り込むことはできません。\n"
                                                 f"・会話に不調を感じる場合は、`{PREFIX}clear`と送信し、会話履歴をリセットしてください。\n"
                                                  "・Discord規約や公序良俗に反する発言を行ったり、Akaneにそのような発言を促す行為を禁止します。",
                                            inline=False)
                            embed.add_field(name="専用コマンド",
                                            value="※以下のコマンドは`#akane-ai`チャンネル内でのみご利用いただけます。\n"
                                                 f"`{'k.chara'.ljust(12)}` AIのキャラクターを変更する\n"
                                                 f"`{'k.clear'.ljust(12)}` 会話履歴のリセット\n"
                                                 f"`{'k.stats'.ljust(12)}` 統計情報の表示",
                                            inline=False)
                            embed.set_footer(text="不具合等連絡先: @bz6")
                            await message.reply(embed=embed)
                            response = gpt(message.content, 0, history, ai_data[1])

                    # 履歴保存
                    if len(response) > 0:
                        if response[0] is True:
                            # 文章モードのみ履歴保存
                            if (len(response[1]) > 0) and (flag == 0):
                                user_dict = {"role": "user", "parts": [message.content]}
                                model_dict = {"role": "model", "parts": [response[1]]}

                                # 30件を超えたら削除（1個目はメッセージカウント）
                                if len(ai_data) >= 31:
                                    del ai_data[2]
                                    del ai_data[2]

                                ai_data.append(user_dict)
                                ai_data.append(model_dict)

                                ai_data[0] += 1

                                with open(f"data/ai/{message.author.id}.json", "w", encoding="UTF-8") as f:
                                    json.dump(ai_data, f)

                                # 文字数が1000を超えたらカット
                                if len(response) > 1000:
                                    response = f"{response[1][:1000]}\n\n※1000文字を超える内容は省略されました※"

                                else:
                                    response = response[1]

                                await message.reply(response, mention_author=False)

                            # 画像モード
                            elif (len(response[1]) > 0) and (flag == 1):
                                ai_data[0] += 1

                                with open(f"data/ai/{message.author.id}.json", "w", encoding="UTF-8") as f:
                                    json.dump(ai_data, f)

                                if len(response) > 1000:
                                    response = f"{response[1][:1000]}\n\n※1000文字を超える内容は省略されました※"

                                else:
                                    response = response[1]

                                await message.reply(response, mention_author=False)

                        else:
                            if str(response[1]).startswith("429"):
                                embed = discord.Embed(title="混雑中",
                                                      description="Akane AIが混雑しています。**5秒程度**お待ちください。",
                                                      color=0xff0000)
                                embed.set_footer(text=f"Report ID: {message.id}")
                                await message.reply(embed=embed, mention_author=False)

                            elif str(response[1]).startswith("500"):
                                embed = discord.Embed(title="混雑中またはエラー",
                                                      description="サーバーが混雑しているか、内部エラーが発生しています。\n"
                                                                  "**30分～1時間程度**時間を空けると完全に解決される場合がありますが、このままご利用いただけます。",
                                                      color=0xff0000)
                                embed.set_footer(text=f"Report ID: {message.id}")
                                await message.reply(embed=embed, mention_author=False)

                            # エラー発生時
                            else:
                                embed = discord.Embed(title="エラー",
                                                      description="不明なエラーが発生しました。しばらく時間を空けるか、メッセージ内容を変えてください。",
                                                      color=0xff0000)
                                embed.set_footer(text=f"Report ID: {message.id}")
                                await message.reply(embed=embed, mention_author=False)

                            if message.attachments:
                                value = "（画像）"

                            else:
                                value = message.content

                            # エラーを専用チャンネルに投げておく async内じゃないので今は動かない
                            error_log = client.get_channel(ERROR_LOG)
                            embed = discord.Embed(title="エラー",
                                                  description="AIチャットにてエラーが発生しました。",
                                                  timestamp=datetime.datetime.now(),
                                                  color=0xff0000)
                            embed.add_field(name="メッセージ内容", value=value)
                            embed.add_field(name="エラー内容", value=response[1])
                            embed.add_field(name="ギルドとチャンネル", value=f"{message.guild.name} (ID: {message.guild.id})\n#{message.channel.id}")
                            embed.add_field(name="ユーザー", value=f"{message.author.mention} (ID: {message.author.id})")
                            embed.set_footer(text=f"Report ID: {message.id}")
                            await error_log.send(embed=embed)

        elif message.channel.name == "akane-quiz":
            # 未実装
            pass
            '''
            if message.content.startswith("::") or message.content.startswith("//"):
                pass

            else:
                async with message.channel.typing():
                    # メッセージカウント
                    if message.content == f"{PREFIX}rating":
                        if os.path.isfile(f"data/quiz/{message.author.id}.json"):
                            with open(f"data/quiz/{message.author.id}.json", "r", encoding="UTF-8") as f:
                                quiz_data = json.load(f)

                            await message.reply(f"レートは{round(quiz_data[0] // 100, 2)}やで",
                                                mention_author=False)

                        else:
                            await message.reply("レートは0.00やで",
                                                mention_author=False)

                        response = ""

                    # 画像データかどうか
                    elif message.attachments:
                        response = ""

                    else:
                        # クイズしたことがあるか
                        if os.path.isfile(f"data/quiz/{message.author.id}.json"):
                            with open(f"data/quiz/{message.author.id}.json", "r", encoding="UTF-8") as f:
                                quiz_data = json.load(f)

                            response = quiz(message.content)

                        # 会話が初めてならjson作成＆インストラクション
                        else:
                            quiz_data = [0]

                            with open(f"data/quiz/{message.author.id}.json", "w", encoding="UTF-8") as f:
                                json.dump(quiz_data, f)

                            embed = discord.Embed(title="Akane AIクイズ",
                                                  description="AIクイズのご利用ありがとうございます。",
                                                  color=discord.Colour.red())
                            embed.add_field(name="注意事項",
                                            value="・クイズをしない場合は、メッセージの先頭に`//`または`::`を付けてください。\n"
                                                  "・Discord規約や公序良俗に反する発言を行ったり、Akaneにそのような発言を促す行為を禁止します。",
                                            inline=False)
                            embed.set_footer(text="不具合等連絡先: @bz6")
                            await message.reply(embed=embed)

                            response = quiz(message.content)

                    # 履歴保存
                    if len(response) > 6:
                        ''' '''
                        r = f"**問題**\n{response[0]}\n\n"
                        f"{response[1]}\n{response[2]}\n"
                        f"{response[3]}\n{response[4]}\n\n"
                        f"答え: ||{response[5]}\n{response[6]}||"
                        await message.reply(r, mention_author=False)
                        ''' '''
                        await message.reply(response, mention_author=False)
                        ''' '''
                        if response[0] == True:
                            quiz_data[0] += 100

                            with open(f'data/quiz/{message.author.id}.json',
                                      'w', encoding='UTF-8') as f:
                                json.dump(quiz_data, f)

                            await message.reply("正解やで（+100）",
                                                mention_author=False)

                        else:
                            if quiz_data[0] > 0:
                                quiz_data[0] -= 50

                            with open(f'data/quiz/{message.author.id}.json',
                                      'w', encoding='UTF-8') as f:
                              json.dump(quiz_data, f)

                            await message.reply("不正解やで（-50）",
                                                mention_author=False)
                        '''

        elif str(message.channel.id) in fxblocked:
            pattern = "https?://[A-Za-z0-9_/:%#$&?()~.=+-]+?(?=" \
                    + "https?:|[^A-Za-z0-9_/:%#$&?()~.=+-]|$)"
            urls = list(set(re.findall(pattern, message.content)))
            twi_pattern = r"https?://(twitter.com|x.com)/([\w/:%#$&\?\(\)~\.=\+\-]+)/status/"

            pattern = re.compile(twi_pattern)

            for i in range(len(urls) - 1, -1, -1):
                if not bool(pattern.search(urls[i])):
                    del urls[i]

                else:
                    u = urls[i] \
                        .replace("twitter.com", "fxtwitter.com", 1) \
                        .replace("x.com", "fixupx.com", 1)
                    m = re.match(twi_pattern, urls[i])
                    urls[i] = f"[ツイート | @{m.group(2)}]({u})"

            if len(urls) > 0:
                urls = urls[:25]
                await message.reply("\n".join(urls), mention_author=False)

    if message.author.id == OWNER:
        if message.content == f"{PREFIX}devhelp":
            desc = "```Akane 管理者用コマンドリスト```\n**管理コマンド**\n`sync`, `devsync`"
            embed = discord.Embed(title="📖コマンドリスト", description=desc)
            await message.reply(embed=embed, mention_author=False)

        if message.content == f"{PREFIX}sync":
            # コマンドをSync
            try:
                await tree.sync()

            except Exception as e:
                embed = discord.Embed(title=":x: エラー",
                                      description="コマンドのSyncに失敗しました",
                                      color=0xff0000)
                embed.add_field(name="エラー内容", value=e)
                await message.reply(embed=embed, mention_author=False)

            else:
                embed = discord.Embed(title=":white_check_mark: 成功",
                                      description="コマンドのSyncに成功しました",
                                      color=discord.Colour.green())
                await message.reply(embed=embed, mention_author=False)

        if message.content == f"{PREFIX}devsync":
            # コマンドをSync
            try:
                await tree.sync(guild=message.guild.id)

            except Exception as e:
                embed = discord.Embed(title=":x: エラー",
                                      description="コマンドのSyncに失敗しました",
                                      color=0xff0000)
                embed.add_field(name="エラー内容", value=e)
                await message.reply(embed=embed, mention_author=False)

            else:
                embed = discord.Embed(title=":white_check_mark: 成功",
                                      description="コマンドのSyncに成功しました",
                                      color=discord.Colour.green())
                await message.reply(embed=embed, mention_author=False)

        if message.content == f"{PREFIX}stop":
            print("[Info] Shutdown is requested by owner")
            embed = discord.Embed(title=":white_check_mark: 成功",
                                  description="Botを停止しています",
                                  color=discord.Colour.green())
            await message.reply(embed=embed, mention_author=False)
            await client.close()


# 全てのインタラクションを取得
@client.event
async def on_interaction(ctx: discord.Interaction):
    try:
        if ctx.data['component_type'] == 2:
            await on_button_click(ctx)
    except KeyError:
        pass


# Buttonの処理
async def on_button_click(ctx: discord.Interaction):
    custom_id = ctx.data["custom_id"]

    if custom_id == "j_g":
        result = random.choice(range(1, 3))

        if result == 1:
            await ctx.response.send_message(f"ぽん:v:{ctx.user.mention}\n君の勝ちやで～")

        elif result == 2:
            await ctx.response.send_message(f"ぽん✊{ctx.user.mention}\nあいこやな。")

        else:
            await ctx.response.send_message(f"ぽん✋{ctx.user.mention}\n私の勝ちやな。また挑戦してや。")

    if custom_id == "j_c":
        result = random.choice(range(1, 3))

        if result == 1:
            await ctx.response.send_message(f"ぽん✋{ctx.user.mention}\n君の勝ちやで～")

        elif result == 2:
            await ctx.response.send_message(f"ぽん:v:{ctx.user.mention}\nあいこやな。")

        else:
            await ctx.response.send_message(f"ぽん✊{ctx.user.mention}\n私の勝ちやな。また挑戦してや。")

    if custom_id == "j_p":
        result = random.choice(range(1, 3))

        if result == 1:
            await ctx.response.send_message(f"ぽん✊{ctx.user.mention}\n君の勝ちやで～")

        elif result == 2:
            await ctx.response.send_message(f"ぽん✋{ctx.user.mention}\nあいこやな。")

        else:
            await ctx.response.send_message(f"ぽん:v:{ctx.user.mention}\n私の勝ちやな。また挑戦してや。")


# Botの起動とDiscordサーバーへの接続
client.run(TOKEN)
