import discord
from discord import app_commands
from discord.ext import commands  # Bot Commands Frameworkをインポート
from yt_dlp import YoutubeDL  # yt-dlp


##################################################

''' コマンド '''


class YouTube(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Cog読み込み時
    @commands.Cog.listener()
    async def on_ready(self):
        print("YouTubeCog on ready")

    #########################

    # yt-dlp

    @app_commands.command(name="ytdl", description="YouTube動画のダウンロードリンクを取得します")
    @app_commands.checks.cooldown(1, 30)
    @app_commands.describe(url="動画URLを指定")
    @app_commands.describe(option="オプションを指定")
    @app_commands.choices(option=[
        discord.app_commands.Choice(name='videoonly', value=1),
        discord.app_commands.Choice(name='soundonly', value=2),
    ])
    async def ytdl(self, ctx: discord.Interaction, url: str,
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

    #########################

    ''' クールダウン '''

    @ytdl.error
    async def on_command_error(self, ctx: discord.Interaction, error: app_commands.AppCommandError):
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
    await bot.add_cog(YouTube(bot))
