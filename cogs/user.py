import re
import datetime

import discord
from discord import app_commands
from discord.ext import commands  # Bot Commands Frameworkをインポート


##################################################

''' コマンド '''


class User(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Cog読み込み時
    @commands.Cog.listener()
    async def on_ready(self):
        print("UserCog on ready")

    #########################

    # userinfo

    @app_commands.command(name="userinfo", description="ユーザー情報を取得するで")
    @app_commands.checks.cooldown(2, 15)
    @app_commands.describe(user="ユーザーをメンションまたはユーザーIDで指定")
    async def userinfo(self, ctx: discord.Interaction, user: str):
        # メンションからID抽出
        target = re.sub("\\D", "", str(user))

        # ユーザーIDからユーザーを取得
        try:
            user = await self.bot.fetch_user(target)

        # できなかったらエラー出す
        except Exception:
            embed = discord.Embed(title=":x: エラー",
                                  description="そのユーザーを取得できませんでした",
                                  color=0xff0000)
            await ctx.response.send_message(embed=embed, ephemeral=True)

        else:
            embed = discord.Embed(title="ID",
                                  description=target,
                                  color=discord.Colour.green())
            try:
                embed.set_author(name=user, icon_url=user.avatar_url)
                embed.set_thumbnail(url=user.avatar_url)

            except Exception:
                pass

            if str(user.discriminator) == "0":
                embed.add_field(name="アカウント名", value=user.name, inline=True)

            else:
                embed.add_field(name="アカウント名", value=f"{user.name}#{user.discriminator}", inline=True)
                # embed.add_field(name="ステータス", value=user.status,inline=True)
                embed.add_field(name="メンション", value=user.mention, inline=True)
                embed.set_footer(text=f"アカウント作成日時: {user.created_at}")

            if hasattr(user.avatar, 'key'):
                embed.set_thumbnail(url=user.avatar.url)

            await ctx.response.send_message(embed=embed)

    # unban

    @app_commands.command(name="unban", description="ユーザーのBAN解除をします")
    @app_commands.checks.cooldown(2, 15)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(user="ユーザーをメンションまたはユーザーIDで指定")
    async def unban(self, ctx: discord.Interaction, user: str):
        if not ctx.guild:
            embed = discord.Embed(title=":x: エラー",
                                  description="このコマンドはDMで使用できません",
                                  color=0xff0000)
            await ctx.response.send_message(embed=embed, ephemeral=True)

        else:
            # メンションからID抽出
            target = re.sub("\\D", "", str(user))

            try:
                user = await self.bot.fetch_user(target)

            # できなかったらエラー出す
            except Exception:
                embed = discord.Embed(title=":x: エラー",
                                      description="そのユーザーを取得できませんでした",
                                      color=0xff0000)
                await ctx.response.send_message(embed=embed, ephemeral=True)

            else:
                try:
                    await ctx.guild.unban(user)

                except Exception:
                    embed = discord.Embed(title=":x: エラー",
                                          description="そのユーザーをBAN解除できません",
                                          color=0xff0000)
                    await ctx.response.send_message(embed=embed, ephemeral=True)

                else:
                    embed = discord.Embed(title=":white_check_mark: 成功",
                                          description="BAN解除が完了しました。\n",
                                          timestamp=datetime.datetime.now(),
                                          color=discord.Colour.green())
                    try:
                        embed.set_thumbnail(url=user.avatar_url)

                    except Exception:
                        pass

                    # if not reason:
                    #     reason = "理由がありません"
                    embed.add_field(name="**BAN解除されたユーザー**",
                                    value=f"{user} [ID:{target}]",
                                    inline=False)
                    # embed.add_field(name="**理由**",
                    #                 value=f"{reason}",
                    #                 inline=False))
                    embed.add_field(name="**実行者**",
                                    value=f"<@!{ctx.author.id}>",
                                    inline=False)
                    await ctx.response.send_message(embed=embed)

    ##################################################

    ''' クールダウン '''

    @userinfo.error
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

    @unban.error
    async def unban_on_command_error(self, ctx: discord.Interaction, error: app_commands.AppCommandError):
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
    await bot.add_cog(User(bot))
