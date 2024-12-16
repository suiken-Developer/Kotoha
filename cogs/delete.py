# 組み込みライブラリ
import datetime

# 外部ライブラリ
import discord
from discord import app_commands
from discord.ext import commands  # Bot Commands Framework


##################################################

''' コマンド '''


class Delete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn_settings = bot.settings_db_connection
        self.c_settings = self.conn_settings.cursor()

    # Cog読み込み時
    @commands.Cog.listener()
    async def on_ready(self):
        print("DeleteCog on ready")

    #########################

    # delete
    @app_commands.command(name="delete", description="10秒以上前のメッセージを削除します")
    @app_commands.checks.cooldown(1, 60)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(num="削除件数を指定 (1~100)")
    async def delete(self, ctx: discord.Interaction, num: int):
        # ephemeral #
        self.c_settings.execute('SELECT ephemeral FROM user_settings WHERE user_id = ?', (ctx.user.id,))
        user_setting = self.c_settings.fetchone()

        if user_setting:
            ephemeral = True if user_setting[0] == 1 else False

        else:
            ephemeral = 0

        #####

        if not ctx.guild:
            embed = discord.Embed(title=":x: エラー",
                                  description="このコマンドはDMで使用できません",
                                  color=0xff0000)
            await ctx.response.send_message(embed=embed, ephemeral=True)

        elif num > 100:
            embed = discord.Embed(title=":x: エラー",
                                  description="100件を超えるメッセージを削除することはできません",
                                  color=0xff0000)
            await ctx.response.send_message(embed=embed, ephemeral=True)

        else:
            channel = ctx.channel
            now = datetime.datetime.now() - datetime.timedelta(seconds=10)
            await ctx.response.defer()

            try:
                deleted = await channel.purge(before=now, limit=int(num), reason=f'{ctx.user}によるコマンド実行')

            except Exception:
                embed = discord.Embed(title=":x: エラー",
                                      description="エラーが発生しました",
                                      color=0xff0000)
                await ctx.followup.send(embed=embed, ephemeral=True)

            else:
                embed = discord.Embed(title=":white_check_mark: 成功",
                                      description=f"`{len(deleted)}`件のメッセージを削除しました",
                                      color=discord.Colour.green())
                await ctx.followup.send(embed=embed, ephemeral=ephemeral)

    #########################

    ''' クールダウン '''

    @delete.error
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
    await bot.add_cog(Delete(bot))
