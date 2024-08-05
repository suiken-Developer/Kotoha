import discord
from discord import app_commands
from discord.ext import commands  # Bot Commands Frameworkをインポート
import qrcode  # qrcode


##################################################

''' 関数群 '''


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


##################################################

''' コマンド '''


class Useful(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Cog読み込み時
    @commands.Cog.listener()
    async def on_ready(self):
        print("UsefulCog on ready")

    #########################

    # QRCode

    @app_commands.command(name="qr", description="QRコード作成")
    @app_commands.checks.cooldown(2, 15)
    async def qr(self, ctx: discord.Interaction):
        await ctx.response.send_modal(QRCode())

    #########################

    ''' クールダウン '''

    @qr.error
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
    await bot.add_cog(Useful(bot))
