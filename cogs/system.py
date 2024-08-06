# 組み込みライブラリ
import os
import datetime
from zoneinfo import ZoneInfo  # JST設定用

# 外部ライブラリ
import discord
from discord import app_commands
from discord.ext import commands  # Bot Commands Framework
import psutil  # psutil
from dotenv import load_dotenv  # python-dotenv
import distro  # distro (Linuxのみ)
import simplejson as json  # simplejson

# 自作モジュール
from modules.pagination import Pagination


load_dotenv()  # .env読み込み

##################################################

''' 定数群 '''

VERSION = os.getenv("VERSION")

##################################################

''' コマンド '''


class System(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Cog読み込み時
    @commands.Cog.listener()
    async def on_ready(self):
        print("SystemCog on ready")

    #########################

    # help

    @app_commands.command(name="help", description="Akaneのコマンド一覧を表示します")
    @app_commands.describe(command="指定したコマンドの説明を表示します")
    async def help(self, ctx: discord.Interaction, command: str = None):

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

    # ping

    @app_commands.command(name="ping", description="AkaneのPingを確認するで")
    async def ping(self, ctx: discord.Interaction):
        embed = discord.Embed(title="Pong!",
                              description=f"`{round(self.bot.latency * 1000, 2)}ms`",
                              color=0xc8ff00)
        await ctx.response.send_message(embed=embed)

    # stats

    @app_commands.command(name="stats", description="Akaneのサーバー情報を見る")
    async def stats(self, ctx: discord.Interaction):
        await ctx.response.defer()

        embed = discord.Embed(title="サーバー情報",
                              description="",
                              color=0xc8ff00)
        embed.add_field(name="CPU", value=f"使用率: {psutil.cpu_percent(interval=1)}% ({round(psutil.cpu_freq().current / 1000, 2)}GHz)\n"
                                          f"温度: {psutil.sensors_temperatures()['coretemp'][0].current}℃")
        embed.add_field(name="RAM", value=f"使用率: {psutil.virtual_memory().percent}% "
                                          f"({round(psutil.virtual_memory().used / 1024 ** 3, 1)}/"
                                          f"{round(psutil.virtual_memory().total / 1024 ** 3, 1)}GB)")
        embed.add_field(name="ストレージ", value=f"使用率: {psutil.disk_usage('/').percent}% "
                        f"({round(psutil.disk_usage('/').used / 1024 ** 3, 1)}/"
                        f"{round(psutil.disk_usage('/').total / 1024 ** 3, 1)}GB)")
        embed.add_field(name="OS", value=f"{distro.name()} {distro.version()}")
        embed.add_field(name="サーバー起動時刻", value=f"{datetime.datetime.fromtimestamp(psutil.boot_time()).strftime('%Y/%m/%d %H:%M:%S')}")
        embed.set_footer(text=f"データ取得時刻: {datetime.datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M:%S')}")
        await ctx.followup.send(embed=embed)

    # invite

    @app_commands.command(name="invite", description="Akaneの招待リンクを表示するで")
    @app_commands.guilds(785105916130754571)
    async def invite(self, ctx: discord.Interaction):
        button = discord.ui.Button(label="招待する", style=discord.ButtonStyle.link,
                                   url="https://discord.com/oauth2/authorize?client_id=777557090562474044")
        embed = discord.Embed(title="招待リンク",
                              description="下のボタンからAkaneを招待できるで！（サーバー管理権限が必要です)",
                              color=0xdda0dd)
        view = discord.ui.View()
        view.add_item(button)
        await ctx.response.send_message(embed=embed, view=view, ephemeral=True)

    #########################

    ''' クールダウン '''

    @stats.error
    async def userinfo_on_command_error(self, ctx: discord.Interaction, error: app_commands.AppCommandError):
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
    await bot.add_cog(System(bot))
