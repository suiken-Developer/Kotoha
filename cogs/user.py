# 組み込みライブラリ
import re
import datetime

# 外部ライブラリ
import discord
from discord import app_commands
from discord.ext import commands  # Bot Commands Framework


##################################################

ALL_BADGES = [["staff", "<:Discord_Staff:1310243625980133416>"],
["partner", "<:Discord_Partner:1310244200222162984>"],
["hypesquad", "<:HypeSquad_Events:1310244618478293002>"],
["bug_hunter", "<:Bug_Hunter:1310244948821413928>"],
["bug_hunter_level_2", "<:Gold_Bug_Hunter:1310246180210343936>"],
["hypesquad_balance", "<:HypeSquad_Balance:1310241795418099792>"],
["hypesquad_bravery", "<:HypeSquad_Bravery:1310242994057908305>"],
["hypesquad_brilliance", "<:HypeSquad_Brilliance:1310243053612830771>"],
["early_supporter", "<:Early_Supporter:1310245165977567232>"],
["verified_bot_developer", "<:Early_Verified_Bot_Developer:1310246728120664205>"],
["discord_certified_moderator", "<:Moderator_Programs_Alumni:1310254854886785137>"],
["active_developer", "<:Active_Developer:1310255185276309677>"]
]

##################################################

''' コマンド '''


class User(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn_settings = bot.settings_db_connection
        self.c_settings = self.conn_settings.cursor()

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
        # ephemeral #
        self.c_settings.execute('SELECT ephemeral FROM user_settings WHERE user_id = ?', (ctx.user.id,))
        user_setting = self.c_settings.fetchone()

        if user_setting:
            ephemeral = True if user_setting[0] == 1 else False

        else:
            ephemeral = 0

        #####

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
            # アカウント名切り分け
            if not user.bot:
                embed = discord.Embed(title=f"@{user.name} の情報",
                                      description="",
                                      color=discord.Colour.green())

                # スパマーフラグ確認
                if user.public_flags.spammer:
                    account_type = "ユーザー (:warning: スパマー)"

                else:
                    account_type = "ユーザー"

            else:
                embed = discord.Embed(title=f"{user.name}#{user.discriminator} の情報",
                                      description="",
                                      color=discord.Colour.green())

                # BOT種別確認
                if user.public_flags.verified_bot:
                    account_type = "認証済みBOT"

                else:
                    account_type = "BOT"

            # 公式か確認
            if user.public_flags.system:
                account_type = "Discord公式"

            try:
                embed.set_thumbnail(url=user.avatar_url)

            except Exception:
                pass

            created_at = int(user.created_at.timestamp()) # アカウント作成日時

            # バッジの所持状況確認
            try:
                owned_badges = [badge[1] for badge in ALL_BADGES if getattr(user.public_flags, badge[0], False)]

                if len(owned_badges) == 0:
                    owned_badges = ["なし"]

            except Exception:
                owned_badges = ["(取得失敗)"]
            
            embed.add_field(name="ユーザーID", value=target, inline=True)
            embed.add_field(name="ニックネーム", value=user.display_name, inline=True)
            embed.add_field(name="メンション", value=user.mention, inline=True)
            embed.add_field(name="バッジ", value=f"{''.join(owned_badges)}", inline=True)
            embed.add_field(name="アカウント種別", value=account_type, inline=True)
            embed.add_field(name="アカウント作成日時", value=f"<t:{created_at}:f> (<t:{created_at}:R>)", inline=True)
            #embed.set_footer(text=f"アカウント作成日時: <t:{created_at}:f> (<t:{created_at}:R>)")

            if hasattr(user.avatar, 'key'):
                embed.set_thumbnail(url=user.avatar.url)

            await ctx.response.send_message(embed=embed, ephemeral=ephemeral)

    # unban

    @app_commands.command(name="unban", description="ユーザーのBAN解除をします")
    @app_commands.checks.cooldown(2, 15)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(user="ユーザーをメンションまたはユーザーIDで指定")
    async def unban(self, ctx: discord.Interaction, user: str):
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
                    await ctx.response.send_message(embed=embed, ephemeral=ephemeral)

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
