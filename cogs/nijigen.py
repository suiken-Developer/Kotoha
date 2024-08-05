import random
import urllib.parse

import discord
from discord import app_commands
from discord.ext import commands  # Bot Commands Frameworkをインポート
from aiodanbooru.api import DanbooruAPI  # aiodanbooru
import requests  # requests


##################################################

''' コマンド '''


class Nijigen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Cog読み込み時
    @commands.Cog.listener()
    async def on_ready(self):
        print("NijigenCog on ready")

    #########################

    # danbooru

    @app_commands.command(name="danbooru", description="Danbooruで画像検索します")
    @app_commands.checks.cooldown(2, 15)
    @app_commands.describe(tags="タグを半角カンマ区切りで指定")
    async def danbooru(self, ctx: discord.Interaction, tags: str = None):
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

    # anime

    @app_commands.command(name="animesearch", description="画像からアニメを特定します")
    @app_commands.checks.cooldown(2, 15)
    @app_commands.describe(image="画像をアップロード")
    async def animesearch(self, ctx: discord.Interaction, image: discord.Attachment):
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

    # クールダウン

    @danbooru.error
    async def danbooru_on_command_error(self, ctx: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.checks.CommandOnCooldown):
            retry_after_int = int(error.retry_after)
            retry_minute = retry_after_int // 60
            retry_second = retry_after_int % 60
            embed = discord.Embed(title="エラー",
                                  description=f"クールダウン中です。\nあと**{retry_minute}分{retry_second}秒**お待ちください。",
                                  color=0xff0000)
            embed.set_footer(text=f"Report ID: {ctx.id}")
            return await ctx.response.send_message(embed=embed, ephemeral=True)

    #########################

    ''' クールダウン '''

    @animesearch.error
    async def animesearch_on_command_error(self, ctx: discord.Interaction, error: app_commands.AppCommandError):
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
    await bot.add_cog(Nijigen(bot))
