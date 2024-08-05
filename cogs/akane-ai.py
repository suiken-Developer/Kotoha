import os
import json
import re
import datetime

import discord
from discord.ui import Select, View
from discord.ext import commands  # Bot Commands Frameworkをインポート
import aiohttp  # aiohttp
from dotenv import load_dotenv  # python-dotenv
import google.generativeai as genai  # google-generativeai


load_dotenv()  # .env読み込み

##################################################

''' 定数群 '''

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # Gemini API Key

VERSION = os.getenv("VERSION")
PREFIX = os.getenv("PREFIX")
ERROR_LOG = int(os.getenv("ERROR_LOG"))  # エラーログを投げるチャンネル
AI_COMMANDS = ["aihelp", "chara", "stats", "clear", "count"]  # 無視するコマンド

##################################################

''' 初期処理 '''

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
AI_COMMANDS = [f"{PREFIX}{i}" for i in AI_COMMANDS]

genai.configure(api_key=GOOGLE_API_KEY)

##################################################

''' 関数群 '''


def help_embed(mode):
    '''
    helpコマンドのembed生成

    Parameters:
    ----------
    mode: int
        0: 初回  1: helpコマンド

    Returns:
    ----------
    embed: discord.Embed()
        embedデータ
    '''
    if mode == 1:
        desc = "AIチャットのヘルプメニューです。"

    else:
        desc = "AIチャットのご利用ありがとうございます。"

    embed = discord.Embed(title="Akane AIチャット",
                          description=desc,
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
                    value="※以下のコマンドはチャットに送信することで使用できます\n"
                         f"`{'k.aihelp'.ljust(12)}` このヘルプ画面を表示する\n"
                         f"`{'k.chara'.ljust(12)}` AIのキャラクターを変更する\n"
                         f"`{'k.clear'.ljust(12)}` 会話履歴のリセット\n"
                         f"`{'k.stats'.ljust(12)}` 統計情報の表示",
                    inline=False)
    embed.set_footer(text="不具合等連絡先: @bz6")

    return embed


def gemini(text, flag, attachment, chara):
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
    image: image
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


# キャラクター選択ドロップダウン
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

''' コマンド '''


class Akane_ai(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Cog読み込み時
    @commands.Cog.listener()
    async def on_ready(self):
        print("akane-aiCog on ready")

    # help
    @commands.command()
    async def aihelp(self, ctx: discord.Interaction):
        embed = help_embed(1)
        await ctx.reply(embed=embed, mention_author=False)

    # count
    @commands.command()
    async def count(self, ctx: discord.Interaction):
        if os.path.isfile(f"data/ai/{ctx.author.id}.json"):
            with open(f"data/ai/{ctx.author.id}.json", "r", encoding='UTF-8') as f:
                ai_data = json.load(f)

            await ctx.reply(f"あなたの総会話回数: {ai_data[0]}回（保存中の会話履歴: 直近{min(len(ai_data) - 2, 30)}件）",
                            mention_author=False)

        else:
            await ctx.reply("あなたの総会話回数: 0回", mention_author=False)

    # clear
    @commands.command()
    async def clear(self, ctx: discord.Interaction):
        if os.path.isfile(f"data/ai/{ctx.author.id}.json"):
            with open(f"data/ai/{ctx.author.id}.json", "r", encoding="UTF-8") as f:
                ai_data = json.load(f)

            count = [int(ai_data[0]), int(ai_data[1])]

            with open(f"data/ai/{ctx.author.id}.json", "w", encoding="UTF-8") as f:
                json.dump(count, f)

            await ctx.reply(":white_check_mark: 会話履歴を削除しました", mention_author=False)

        else:
            await ctx.reply(":x: まだ会話を行っていません", mention_author=False)

    # chara
    @commands.command()
    async def chara(self, ctx: discord.Interaction):
        if os.path.isfile(f"data/ai/{ctx.author.id}.json"):
            with open(f"data/ai/{ctx.author.id}.json", "r", encoding="UTF-8") as f:
                ai_data = json.load(f)

            view = SelectView()

            # キャラクター削除対応
            if ai_data[1] > len(CHARAS) - 1:
                chara_present = CHARAS[0]

            else:
                chara_present = CHARAS[ai_data[1]]

            await ctx.reply("変更するキャラクターを選択してください\n"
                            f"現在のキャラクター: **{chara_present}**\n\n"
                            ":warning: キャラクターを変更すると会話履歴がリセットされます", view=view)

        else:
            await ctx.reply(":x: まだ会話を行っていません", mention_author=False)

    # stats
    @commands.command()
    async def stats(self, ctx: discord.Interaction):
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
            await ctx.reply(":x: エラーが発生しました", mention_author=False)

        else:
            embed = discord.Embed(title="Akane AI 統計情報",
                                  description=f"**総会話回数**\n{total_talks}回\n\n"
                                              f"**総ユーザー数**\n{total_users}人\n\n"
                                              f"**AIモデル**\n{AIMODEL_NAME}\n\n",
                                  color=discord.Colour.green())
            embed.set_footer(text=f"Akane v{VERSION}")
            await ctx.reply(embed=embed, mention_author=False)

    # #akane-ai
    @commands.Cog.listener("on_message")
    async def ai_talk(self, message):
        # Bot, 全体メンション, DM, 特定Prefix, コマンドは無視
        if message.author.bot or message.mention_everyone or \
                isinstance(message.channel, discord.DMChannel) or \
                message.content.startswith("::") or message.content.startswith("//") or \
                message.content in AI_COMMANDS:
            return

        # メイン処理
        if message.channel.name == "akane-ai":
            async with message.channel.typing():
                # 画像データかどうか（画像は過去ログ使用不可）
                if message.attachments:
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

                                            embed = help_embed()
                                            await message.reply(embed=embed)

                                        response = gemini(cleaned_text, 1, image_data, chara)

                        else:
                            await message.reply(":x: 画像が読み取れません。ファイルを変更してください。\n"
                                                "対応しているファイル形式: ```.png .jpg .jpeg .gif .webp```",
                                                mention_author=False)
                            response = ""

                else:
                    # 文章モード (過去データ読み取り)
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
                        response = gemini(message.content, 0, history, ai_data[1])

                    # 会話が初めてならjson作成＆インストラクション
                    else:
                        ai_data = [0, 0]
                        history = []

                        with open(f"data/ai/{message.author.id}.json", "w", encoding="UTF-8") as f:
                            json.dump(ai_data, f)

                        embed = help_embed(0)
                        await message.reply(embed=embed)
                        response = gemini(message.content, 0, history, ai_data[1])

                # 正常な返答があれば履歴保存
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
                        # エラーログ出力
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

                        # 例外エラー
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

                        # エラーを専用チャンネルに投げておく
                        error_log = self.bot.get_channel(ERROR_LOG)
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

    #########################

    # エラー出力
    async def cog_command_error(self, ctx: discord.Interaction, error):
        embed = discord.Embed(title="エラー",
                              description="不明なエラーが発生しました。",
                              color=0xff0000)
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Akane_ai(bot))
