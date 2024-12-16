# 外部ライブラリ
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
        self.conn_settings = bot.settings_db_connection
        self.c_settings = self.conn_settings.cursor()

    # Cog読み込み時
    @commands.Cog.listener()
    async def on_ready(self):
        print("UsefulCog on ready")

    #########################

    # QRCode

    @app_commands.command(name="qr", description="QRコードを作成します")
    @app_commands.checks.cooldown(2, 15)
    async def qr(self, ctx: discord.Interaction):
        await ctx.response.send_modal(QRCode())

    # text

    @app_commands.command(name="text", description="半角英数文字列を装飾文字に変換します")
    @app_commands.describe(txt_type="装飾文字の種類")
    @app_commands.describe(text="文字列を入力")
    @app_commands.choices(txt_type=[
        discord.app_commands.Choice(name="𝐁𝐨𝐥𝐝", value="bold"),
        discord.app_commands.Choice(name="𝐼𝑡𝑎𝑙𝑖𝑐", value="italic"),
        discord.app_commands.Choice(name="𝑩𝒐𝒍𝒅 𝑰𝒕𝒂𝒍𝒊𝒄", value="bolditalic"),
        discord.app_commands.Choice(name="𝗕𝗼𝗹𝗱 (𝗦𝗮𝗻𝘀)", value="sansbold"),
        discord.app_commands.Choice(name="𝘐𝘵𝘢𝘭𝘪𝘤 (𝘚𝘢𝘯𝘴)", value="sansitalic"),
        discord.app_commands.Choice(name="𝑩𝒐𝒍𝒅 𝑰𝒕𝒂𝒍𝒊𝒄 (𝑺𝒂𝒏𝒔)", value="sansbolditalic"),
        discord.app_commands.Choice(name="𝒞𝓊𝓇𝓈𝒾𝓋ℯ 𝒮𝒸𝓇𝒾𝓅𝓉", value="cursive"),
        discord.app_commands.Choice(name="𝓒𝓾𝓻𝓼𝓲𝓿𝓮 𝓢𝓬𝓻𝓲𝓹𝓽 (𝓑𝓸𝓵𝓭)", value="cursivebold"),
        discord.app_commands.Choice(name="𝔉𝔯𝔞𝔨𝔱𝔲𝔯", value="fraktur"),
        discord.app_commands.Choice(name="𝕱𝖗𝖆𝖐𝖙𝖚𝖗 (𝕭𝖔𝖑𝖉)", value="frakturbold")])
    async def text(self, ctx: discord.Interaction, txt_type: str, text: str):
        # Unicodeの開始ポイント
        unicode_styles = {
            "bold": (0x1D41A, 0x1D400),  # 太字
            "italic": (0x1D44E, 0x1D434),  # 斜体
            "bolditalic": (0x1D482, 0x1D468),  # 太字+斜体
            "sansbold": (0x1D5BA, 0x1D5A0),  # Sans Serif 太字
            "sansitalic": (0x1D608, 0x1D622),  # Sans Serif 斜体
            "sansbolditalic": (0x1D656, 0x1D63C), # Sans Serif 太字+斜体
            "cursive": (0x1D4B6, 0x1D49C), # Cursive Script
            "cursivebold": (0x1D4EA, 0x1D4D0), # Cursive Script 太字
            "fraktur": (0x1D51E, 0x1D504), # Fraktur
            "frakturbold": (0x1D586, 0x1D56C) # Fraktur 太字
        }

        start, end = unicode_styles[txt_type]
        result = ""

        for char in text:
            if "a" <= char <= "z":  # 小文字
                result += chr(start + ord(char) - ord("a"))
            elif "A" <= char <= "Z":  # 大文字
                result += chr(end + ord(char) - ord("A"))
            else:
                result += char  # 非英字はそのまま

        await ctx.response.send_message(result, ephemeral=True)

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
