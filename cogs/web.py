import json
import os

import discord
from discord import app_commands
from discord.ext import commands  # Bot Commands Framework
import requests  # requests
from dotenv import load_dotenv  # python-dotenv


load_dotenv()  # .env読み込み

##################################################

''' 定数群 '''

UR7_USERNAME = os.getenv("UR7_USERNAME")  # ur7.cc
UR7_PASSWORD = os.getenv("UR7_PASSWORD")  # ur7.cc

##################################################

''' 関数群 '''


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
        url = f"https://gsapi.cbrx.io/image?top={self.line1.value}&bottom={self.line2.value}&type=png"

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


##################################################

''' コマンド '''


class Web(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Cog読み込み時
    @commands.Cog.listener()
    async def on_ready(self):
        print("WebCog on ready")

    #########################

    # url

    @app_commands.command(name="url", description="URLを短縮します")
    @app_commands.checks.cooldown(2, 15)
    @app_commands.describe(url="URLを貼り付け")
    async def url(self, ctx: discord.Interaction, url: str):
        await ctx.response.defer()

        request = requests.post(
            f"https://ur7.cc/yourls-api.php?username={UR7_USERNAME}&password={UR7_PASSWORD}&action=shorturl&format=json&url={url}"
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

    # 5000choen

    @app_commands.command(name="gosen", description="「5000兆円欲しい！」ジェネレーター")
    @app_commands.checks.cooldown(2, 15)
    async def gosen_choen(self, ctx: discord.Interaction):
        await ctx.response.send_modal(GosenChoen())

    ##################################################

    ''' クールダウン '''

    @url.error
    async def url_on_command_error(self, ctx: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.checks.CommandOnCooldown):
            retry_after_int = int(error.retry_after)
            retry_minute = retry_after_int // 60
            retry_second = retry_after_int % 60
            embed = discord.Embed(title="エラー",
                                  description=f"クールダウン中です。\nあと**{retry_minute}分{retry_second}秒**お待ちください。",
                                  color=0xff0000)
            embed.set_footer(text=f"Report ID: {ctx.id}")
            return await ctx.response.send_message(embed=embed, ephemeral=True)

    @gosen_choen.error
    async def gosen_choen_on_command_error(self, ctx: discord.Interaction, error: app_commands.AppCommandError):
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
    await bot.add_cog(Web(bot))
