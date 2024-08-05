import discord
from discord import app_commands
from discord.ext import commands  # Bot Commands Framework


##################################################

''' コマンド '''


class Guild(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Cog読み込み時
    @commands.Cog.listener()
    async def on_ready(self):
        print("GuildCog on ready")

    #########################

    # GuildIcon

    @app_commands.command(name="getguildicon", description="このサーバーのアイコンを取得します")
    @app_commands.checks.cooldown(2, 15)
    async def getguildicon(self, ctx: discord.Interaction):
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

    #########################

    ''' クールダウン '''

    @getguildicon.error
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
    await bot.add_cog(Guild(bot))
