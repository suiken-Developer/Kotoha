import os
import json
import datetime
from zoneinfo import ZoneInfo  # JST設定用

import discord
from discord import app_commands
from discord.ext import commands  # Bot Commands Frameworkをインポート
from dotenv import load_dotenv  # python-dotenv

from modules.shika import shika


load_dotenv()  # .env読み込み

##################################################

''' 定数群 '''

# エラーログ
ERROR_LOG = int(os.getenv("ERROR_LOG"))

##################################################

''' コマンド '''


class Shikanoko(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    # Cog読み込み時
    @commands.Cog.listener()
    async def on_ready(self):
        print("ShikanokoCog on ready")


    #########################


    # shikanoko
    @app_commands.command(name="shikanoko", description="「しかのこのこのここしたんたん」を引き当てよう")
    @app_commands.checks.cooldown(1, 1)
    @app_commands.describe(pcs="回数（1~20）")
    async def shikanoko(self, ctx: discord.Interaction, pcs: int = 1):
        # エラー: 回数が範囲外
        if not 0 < pcs < 21:
            embed = discord.Embed(title=":x: エラー",
                                description="回数は1~20で指定してください",
                                color=0xff0000)
            await ctx.response.send_message(embed=embed, ephemeral=True)

        else:
            await ctx.response.defer()

            with open("data/shikanoko.json", "r", encoding="UTF-8") as f:
                data = json.load(f)

            data['total'] += pcs

            if pcs > 1:
                results = []

                for i in range(pcs):
                    c = "し"
                    words = [c]

                    while True:
                        c = shika(c)

                        if c == "END":
                            word = "".join(words)
                            results.append(word)
                            break

                        else:
                            words.append(c)

                if "しかのこのこのここしたんたん" in results:
                    n = results.count("しかのこのこのここしたんたん")
                    status = "あたり！"
                    data['win'] += n
                    data['latest'] = f"@{ctx.user.name}"

                    # 当選データベースに登録
                    if str(ctx.user.id) in data['ranking'].values():
                        data['ranking'][str(ctx.user.id)] += n

                    else:
                        data['ranking'][str(ctx.user.id)] = n

                else:
                    status = "はずれ！"

                # 結果を変数にまとめる
                result = ""

                for i in results:
                    result += f"・{i}\n"

                probability = round((data['win'] / data['total']) * 100, 2)
                embed = discord.Embed(title=":deer: しかのこのこのここしたんたん",
                                      description=f"{result}\n**{status}**",
                                      color=discord.Colour.green())
                embed.set_footer(text=f"統計: {data['win']}/{data['total']}回当たり ({probability}%)  直近の当選者: {data['latest']}")
                await ctx.followup.send(embed=embed)

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
                    data['win'] += 1
                    data['latest'] = f"@{ctx.user.name}"

                    # 当選データベースに登録
                    if str(ctx.author.id) in data['ranking'].values():
                        data['ranking'][str(ctx.user.id)] += 1

                    else:
                        data['ranking'][str(ctx.user.id)] = 1

                else:
                    status = "はずれ！"

                probability = round((data['win'] / data['total']) * 100, 2)
                embed = discord.Embed(title=":deer: しかのこのこのここしたんたん",
                                      description=f"{word}\n\n**{status}**",
                                      color=discord.Colour.green())
                embed.set_footer(text=f"統計: {data['win']}/{data['total']}回当たり ({probability}%)  直近の当選者: {data['latest']}")
                await ctx.followup.send(embed=embed)

            # データの保存
            with open("data/shikanoko.json", "w", encoding="UTF-8") as f:
                json.dump(data, f)


    # shikaoko-ranking
    @app_commands.command(name="shikanoko-ranking", description="ランキング情報")
    @app_commands.checks.cooldown(2, 60)
    async def shikanoko_ranking(self, ctx: discord.Interaction):
        await ctx.response.defer()

        # データ読み込み
        with open("data/shikanoko.json", "r", encoding="UTF-8") as f:
            data = json.load(f)

        ranking = sorted(data["ranking"].items(), key=lambda x: x[1], reverse=True)
        # longest_ranking = sorted(data["longest_ranking"].items(), key=lambda x: x[1], reverse=True)

        # embedデータの作成
        desc = "**[出現回数トップ10]**\n"

        # トップ10の作成
        current_rank = 1
        previous_value = None
        count = 0
        your_rank = "集計対象外"

        for i, (key, value) in enumerate(ranking):
            # 値が異なる場合は順位+1
            if value != previous_value:
                if count >= 10:
                    break

                current_rank = i + 1

            # 自分の順位回収
            if key == str(ctx.user.id):
                your_rank = f"{current_rank}位 @{ctx.user.name}  **{value}回**"

            if count < 10:
                # ユーザー名に変換
                try:
                    user = await self.bot.fetch_user(int(key))

                except Exception:
                    name = "不明なユーザー"

                else:
                    name = user.name

                desc += f"{current_rank}位: @{name}  **{value}回**\n"
                count += 1

            previous_value = value

        desc += f"\n**[あなたの順位]**\n{your_rank}"

        embed = discord.Embed(title="🦌「しかのこ」ランキング",
                              description=desc,
                              color=discord.Colour.green())
        embed.set_footer(text=f"ランキング取得時刻: {datetime.datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M:%S')}")
        await ctx.followup.send(embed=embed)


    #########################

    ''' クールダウン '''


    @shikanoko.error
    async def shikanoko_on_command_error(self, ctx: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.checks.CommandOnCooldown):
            retry_after_int = int(error.retry_after)
            retry_minute = retry_after_int // 60
            retry_second = retry_after_int % 60
            embed = discord.Embed(title="エラー",
                                  description=f"クールダウン中です。\nあと**{retry_minute}分{retry_second}秒**お待ちください。",
                                  color=0xff0000)
            embed.set_footer(text=f"Report ID: {ctx.id}")
            return await ctx.response.send_message(embed=embed, ephemeral=True)


    @shikanoko_ranking.error
    async def ranking_on_command_error(self, ctx: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.checks.CommandOnCooldown):
            retry_after_int = int(error.retry_after)
            retry_minute = retry_after_int // 60
            retry_second = retry_after_int % 60
            embed = discord.Embed(title="エラー",
                                  description=f"クールダウン中です。\nあと**{retry_minute}分{retry_second}秒**お待ちください。",
                                  color=0xff0000)
            embed.set_footer(text=f"Report ID: {ctx.id}")
            return await ctx.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Shikanoko(bot))