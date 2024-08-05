import random

import discord
from discord import app_commands
from discord.ext import commands  # Bot Commands Frameworkをインポート


##################################################

''' コマンド '''


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Cog読み込み時
    @commands.Cog.listener()
    async def on_ready(self):
        print("FunCog on ready")

    #########################

    # cat
    @app_commands.command(name="cat", description="ﾈｺﾁｬﾝ")
    async def cat(self, ctx: discord.Interaction):
        nekos = ["🐱( '-' 🐱 )ﾈｺﾁｬﾝ", "ﾆｬﾝฅ(>ω< )ฅﾆｬﾝ♪",
                 "ฅ•ω•ฅﾆｬﾆｬｰﾝ✧", "ฅ( ̳• ·̫ • ̳ฅ)にゃあ",
                 "ﾆｬｯ(ฅ•ω•ฅ)", "ฅ•ω•ฅにぁ？",
                 "( ฅ•ω•)ฅ ﾆｬｰ!", "ฅ(´ω` ฅ)ﾆｬｰ",
                 "(/・ω・)/にゃー!",
                 "(*´ω｀*ฅ)ﾆｬｰ", "ฅ^•ω•^ฅﾆｬｰ",
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

    # dice

    @app_commands.command(name="dice", description="サイコロを振るで")
    @app_commands.describe(pcs="サイコロの個数（1~100）")
    @app_commands.describe(maximum="サイコロの最大値（1～999）")
    async def dice(self, ctx: discord.Interaction, pcs: int = 1, maximum: int = 6):
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

    # kuji

    @app_commands.command(name="kuji", description="おみくじ")
    @app_commands.describe(pcs="引く枚数（1~100）")
    async def kuji(self, ctx: discord.Interaction, pcs: int = 1):
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

    # じゃんけん

    @app_commands.command(name="janken", description="じゃんけん")
    async def janken(self, ctx: discord.Interaction):
        button1 = discord.ui.Button(label="ぐー", style=discord.ButtonStyle.primary, custom_id="j_g")
        button2 = discord.ui.Button(label="ちょき", style=discord.ButtonStyle.success, custom_id="j_c")
        button3 = discord.ui.Button(label="ぱー", style=discord.ButtonStyle.danger, custom_id="j_p")
        view = discord.ui.View()
        view.add_item(button1)
        view.add_item(button2)
        view.add_item(button3)
        await ctx.response.send_message("最初はぐー、じゃんけん", view=view)

    #########################

    # エラー出力

    async def cog_command_error(self, ctx: discord.Interaction, error):
        embed = discord.Embed(title="エラー",
                              description="不明なエラーが発生しました。",
                              color=0xff0000)
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))
