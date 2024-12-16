# 組み込みライブラリ
import datetime

# 外部ライブラリ
import discord
from discord import app_commands
from discord.ext import commands  # Bot Commands Framework
from discord.ext import tasks


##################################################

''' コマンド '''


class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.settings_db_connection
        self.c = self.conn.cursor()

        # user_settingsテーブルの作成
        self.c.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            language TEXT,
            timezone FLOAT,
            ephemeral INTEGER,
            spotify_time INTEGER,
            spotify_total_time INT DEFAULT 0,
            game_time INTEGER
        )
        ''')

        # guild_settingsテーブルの作成
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                language TEXT,
                timezone FLOAT
            )
        ''')

        self.conn.commit()

    # Cog読み込み時
    @commands.Cog.listener()
    async def on_ready(self):
        print("SettingCog on ready")

    #########################
    '''
    @tasks.loop(minutes=5)
    async def activity_tracker(self):
        self.c.execute("SELECT user_id FROM user_settings WHERE spotify_time = 1")
        user_ids = [row[0] for row in self.c.fetchall()]
        plus_user_ids = []

        for guild in self.bot.guilds:
            for member in guild.members:
                if member.id in user_ids and member.status in (discord.Status.online, discord.Status.dnd):
                    for activity in member.activities:
                        if isinstance(activity, discord.Spotify):
                            plus_user_ids.append(member.id)

        self.c.executemany("UPDATE user_settings SET spotify_total_time = spotify_total_time + 5 WHERE user_id = ?", [(user_id,) for user_id in plus_user_ids])
        self.conn.commit()'''

    #########################

    # /settingsコマンドをグループ化
    group = app_commands.Group(name="setting", description="ユーザー設定コマンド")

    # info

    @group.command(name="info", description="Akaneの個人設定、サーバー設定（管理者のみ）を表示します")
    @app_commands.checks.cooldown(2, 15)
    async def info(self, ctx: discord.Interaction):
        # DBでuser_idが存在するか確認
        self.c.execute('SELECT language, timezone, ephemeral, spotify_time, game_time FROM user_settings WHERE user_id = ?', (ctx.user.id,))
        result = self.c.fetchone()

        if not result:
            # 未設定の場合初期値を与えておく
            result = ["未設定", "未設定", 0, 0, 0]

        description = f"言語: **{result[0] or '未設定'}**\n" \
                    + f"タイムゾーン: **{result[1] or '未設定'}**\n" \
                    + f"コマンドの出力(一部非対応): **{'非公開' if result[2] == 1 else '公開'}**\n" \
                    + f"Spotifyの再生時間を記録: **{'有効' if result[3] == 1 else '無効'}**\n" \
                    + f"ゲームのプレイ時間を記録: **{'有効' if result[4] == 1 else '無効'}**\n"

        embed = discord.Embed(title=f"設定情報",
                            description="",
                            color=discord.Colour.green())
        
        embed.add_field(name="個人設定", value=description, inline=False)

        # サーバーでの実行かつ管理者なら
        if ctx.guild and ctx.user.guild_permissions.administrator:
            # DBでguild_idが存在するか確認
            self.c.execute('SELECT language, timezone FROM guild_settings WHERE guild_id = ?', (ctx.guild.id,))
            guild_result = self.c.fetchone()

            if not guild_result:
                # 未設定の場合初期値を与えておく
                guild_result = ["未設定", "未設定"]

            guild_description = f"言語: **{guild_result[0]}**\n" \
                        + f"タイムゾーン: **{guild_result[1]}**\n" \
                        + "※個人設定がある場合はそちらが優先されます"
            
            embed.add_field(name="サーバー設定", value=guild_description, inline=False)

        await ctx.response.send_message(embed=embed, ephemeral=True if result[2] == 1 else False)

    # visibility

    @group.command(name="visibility", description="【コマンド出力の公開・非公開】設定を切り替えます")
    @app_commands.checks.cooldown(2, 15)
    @app_commands.describe(visible="表示するかどうか")
    @app_commands.choices(visible=[
        discord.app_commands.Choice(name="公開", value="False"),
        discord.app_commands.Choice(name="非公開", value="True"),])
    async def visibility(self, ctx: discord.Interaction, visible: str):
        # DBでuser_idが存在するか確認
        self.c.execute('SELECT ephemeral FROM user_settings WHERE user_id = ?', (ctx.user.id,))
        result = self.c.fetchone()

        if result:
            # Trueの場合
            if visible == "True":
                setting = 1

            else:
                setting = 0

            self.c.execute('''
                           UPDATE user_settings
                           SET ephemeral = ?
                           WHERE user_id = ?
                           ''', (setting, ctx.user.id))
            self.conn.commit()

        else:
            # Trueの場合
            if visible == "True":
                setting = 1

            else:
                setting = 0

            self.c.execute('''
                INSERT INTO user_settings (user_id, language, timezone, ephemeral, spotify_time, spotify_total_time, game_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (ctx.user.id, "", "", setting, 0, 0, 0))
            self.conn.commit()

        embed = discord.Embed(title=":white_check_mark: 設定完了",
                              description=f"【コマンド出力の表示・非表示】を**{'非公開' if setting == 1 else '公開'}**に設定しました",
                              color=discord.Colour.green())

        await ctx.response.send_message(embed=embed, ephemeral=True if setting == 1 else False)

    # spotify

    @group.command(name="spotify", description="【Spotifyの再生時間を記録】設定を切り替えます")
    @app_commands.checks.cooldown(2, 15)
    @app_commands.describe(enable="有効化するかどうか")
    @app_commands.choices(enable=[
        discord.app_commands.Choice(name="有効", value="True"),
        discord.app_commands.Choice(name="無効", value="False"),])
    async def spotify(self, ctx: discord.Interaction, enable: str):
        # DBでuser_idが存在するか確認
        self.c.execute('SELECT ephemeral FROM user_settings WHERE user_id = ?', (ctx.user.id,))
        result = self.c.fetchone()

        if result:
            ephemeral = result[0]

            # Trueの場合
            if enable == "True":
                setting = 1

            else:
                setting = 0

            self.c.execute('''
                           UPDATE user_settings
                           SET spotify_time = ?
                           WHERE user_id = ?
                           ''', (setting, ctx.user.id))
            self.conn.commit()

        else:
            ephemeral = 0

            # Trueの場合
            if enable:
                setting = 1

            else:
                setting = 0

            self.c.execute('''
                INSERT INTO user_settings (user_id, language, timezone, ephemeral, spotify_time, spotify_total_time, game_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (ctx.user.id, "", "", ephemeral, setting, 0, 0))
            self.conn.commit()

        embed = discord.Embed(title=":white_check_mark: 設定完了",
                              description=f"【Spotifyの再生時間を記録】を**{'有効' if setting == 1 else '無効'}**に設定しました",
                              color=discord.Colour.green())

        await ctx.response.send_message(embed=embed, ephemeral=True if ephemeral == 1 else False)

    ##################################################

    ''' クールダウン '''

    @info.error
    async def info_on_command_error(self, ctx: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.checks.CommandOnCooldown):
            retry_after_int = int(error.retry_after)
            retry_minute = retry_after_int // 60
            retry_second = retry_after_int % 60
            embed = discord.Embed(title="エラー",
                                  description=f"クールダウン中です。\nあと**{retry_minute}分{retry_second}秒**お待ちください。",
                                  color=0xff0000)
            embed.set_footer(text=f"Report ID: {ctx.id}")
            return await ctx.response.send_message(embed=embed, ephemeral=True)

    @spotify.error
    async def spotify_on_command_error(self, ctx: discord.Interaction, error: app_commands.AppCommandError):
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
    await bot.add_cog(Settings(bot))
