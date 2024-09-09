# 組み込みライブラリ
import os
import datetime
from zoneinfo import ZoneInfo  # JST設定用
import sqlite3

# 外部ライブラリ
import discord
from discord import app_commands
from discord.ext import commands  # Bot Commands Framework
from dotenv import load_dotenv  # python-dotenv
import simplejson as json  # simplejson

# 自作モジュール
from modules.shika import shika


load_dotenv()  # .env読み込み

##################################################

''' 定数群 '''

# エラーログ
ERROR_LOG = int(os.getenv("ERROR_LOG"))

##################################################

''' コマンド '''


class Shikanoko(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect('data/shikanoko.db')
        self.c = self.conn.cursor()

        # money.dbの共有接続を取得
        self.money_conn = bot.money_db_connection
        self.money_c = self.money_conn.cursor()

        # ユーザー情報を保存するテーブルを作成
        self.c.execute('''
        CREATE TABLE IF NOT EXISTS user_lucky_draw (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            hits INTEGER DEFAULT 0,
            last_hit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 最新のあたりユーザーを保存するテーブルを作成
        self.c.execute('''
        CREATE TABLE IF NOT EXISTS latest_winner (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            username TEXT
        )
        ''')

        # 総あたり回数を保存するテーブルを作成
        self.c.execute('''
        CREATE TABLE IF NOT EXISTS total_hits (
            id INTEGER PRIMARY KEY,
            total_hits INTEGER DEFAULT 0,
            total_draws INTEGER DEFAULT 0
        )
        ''')

        # 初期化：総あたり回数と総実行回数が記録されていない場合は初期値を設定
        self.c.execute('SELECT total_hits, total_draws FROM total_hits WHERE id = 1')
        if self.c.fetchone() is None:
            self.c.execute('INSERT INTO total_hits (id, total_hits, total_draws) VALUES (1, 0, 0)')
            self.conn.commit()

    # Cog読み込み時
    @commands.Cog.listener()
    async def on_ready(self):
        print("ShikanokoCog on ready")

    #########################

    # shikanoko

    @app_commands.command(name="shikanoko", description="「しかのこのこのここしたんたん」を引き当てよう")
    @app_commands.checks.cooldown(1, 1)
    @app_commands.describe(pcs="回数（1~20）")
    async def shikanoko(self, ctx: discord.Interaction, pcs: int = 1):
        # エラー: 回数が範囲外
        if not 0 < pcs < 21:
            embed = discord.Embed(title=":x: エラー",
                                description="回数は1~20で指定してください",
                                color=0xff0000)
            await ctx.response.send_message(embed=embed, ephemeral=True)

        else:
            results = []

            for i in range(pcs):
                c = "し"
                words = [c]

                while True:
                    c = shika(c)

                    if c == "END":
                        word = "".join(words)
                        results.append(word)
                        break

                    else:
                        words.append(c)

            if "しかのこのこのここしたんたん" in results:
                n = results.count("しかのこのこのここしたんたん")
                status = "**あたり！**\n※ウォレットを開設していれば報酬が受け取れます"

                # 最新のあたりユーザーを更新
                self.c.execute('DELETE FROM latest_winner')
                self.c.execute('INSERT INTO latest_winner (user_id, username) VALUES (?, ?)',
                            (ctx.user.id, ctx.user.name))

                # ユーザーのあたり回数を更新
                self.c.execute('SELECT hits FROM user_lucky_draw WHERE user_id = ?', (ctx.user.id,))
                row = self.c.fetchone()

                if row is None:
                    # 新規ユーザーの場合
                    self.c.execute('INSERT INTO user_lucky_draw (user_id, username, hits) VALUES (?, ?, ?)',
                                (ctx.user.id, ctx.user.name, n))
                else:
                    # 既存ユーザーの場合、あたり回数とユーザー名を更新
                    self.c.execute(f'''
                    UPDATE user_lucky_draw
                    SET hits = hits + {n}, last_hit_time = CURRENT_TIMESTAMP, username = ?
                    WHERE user_id = ?
                    ''', (ctx.user.name, ctx.user.id))

                # 総あたり回数を更新
                self.c.execute(f'UPDATE total_hits SET total_hits = total_hits + {n} WHERE id = 1')

                # DBをチェックして報酬を与える
                self.money_c.execute('SELECT balance FROM user_data WHERE user_id = ?', (ctx.user.id,))
                result = self.money_c.fetchone()

                if result:
                    bonus = 3000 * n

                    self.money_c.execute('''
                        UPDATE user_data
                        SET balance = ?
                        WHERE user_id = ?
                    ''', ((result[0] + bonus), ctx.user.id))

                    self.money_conn.commit()

                    status = f"**あたり！**\n{bonus} ZNY獲得"

            else:
                status = "**はずれ！**"

            # 総実行回数を更新
            self.c.execute(f'UPDATE total_hits SET total_draws = total_draws + {pcs} WHERE id = 1')
            self.conn.commit()

            # 総あたり回数と総実行回数を表示
            self.c.execute('SELECT total_hits, total_draws FROM total_hits WHERE id = 1')
            total_hits, total_draws = self.c.fetchone()

            # あたり者も表示
            self.c.execute('SELECT username FROM latest_winner')
            latest_winner = self.c.fetchone()

            if latest_winner:
                latest_winner = latest_winner[0]

            else:
                latest_winner = "なし"

            # 結果を変数にまとめる
            result = ""

            for i in results:
                result += f"・{i}\n"

            probability = round((total_hits / total_draws) * 100, 2)
            embed = discord.Embed(title=":deer: しかのこのこのここしたんたん",
                                    description=f"{result}\n{status}",
                                    color=discord.Colour.green())
            embed.set_footer(text=f"統計: {total_hits}/{total_draws}回当たり ({probability}%)  直近の当選者: @{latest_winner}")
            await ctx.response.send_message(embed=embed)

    # shikanoko-ranking

    @app_commands.command(name="shikanoko-ranking", description="ランキング情報")
    @app_commands.checks.cooldown(2, 60)
    async def shikanoko_ranking(self, ctx: discord.Interaction):
        # データ読み込み

        # トップ10のユーザーを取得
        self.c.execute('''
        SELECT user_id, hits FROM user_lucky_draw
        ORDER BY hits DESC
        LIMIT 10
        ''')
        top10_rows = self.c.fetchall()

        top10_users = []
        rank = 1
        previous_hits = None
        current_rank = 1

        # トップ10のユーザーの順位を決定
        for id, hits in top10_rows:
            # データベースから最新のユーザー名を取得
            self.c.execute('SELECT username FROM user_lucky_draw WHERE user_id = ?', (id,))
            username = self.c.fetchone()[0]

            # 順位の重複処理
            if previous_hits is None or hits < previous_hits:
                current_rank = rank

            rank += 1
            previous_hits = hits

            top10_users.append(f"{current_rank}位: `@{username}`  **{hits}**回")

        # 自分の順位を取得
        self.c.execute('''
        SELECT COUNT(*) + 1 FROM user_lucky_draw
        WHERE hits > (SELECT hits FROM user_lucky_draw WHERE user_id = ?)
        ''', (ctx.user.id,))
        user_rank = self.c.fetchone()[0]

        # 自分のあたり回数を取得
        self.c.execute('SELECT hits FROM user_lucky_draw WHERE user_id = ?', (ctx.user.id,))
        user_hits = self.c.fetchone()

        # 自分の順位とあたり回数を表示
        if user_hits:
            user_rank_data = f"{user_rank}位: `@{ctx.user.name}`  **{user_hits[0]}**回"

        else:
            user_rank_data = "集計対象外"

        # embedデータの作成
        desc = "**[出現回数トップ10]**\n"

        for i in top10_users:
            desc += f"{i}\n"

        desc += f"\n**[あなたの順位]**\n{user_rank_data}"

        embed = discord.Embed(title="🦌「しかのこ」ランキング",
                            description=desc,
                            color=discord.Colour.green())
        embed.set_footer(text=f"ランキング取得時刻: {datetime.datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M:%S')}")
        await ctx.response.send_message(embed=embed)

    #########################

    ''' クールダウン '''

    @shikanoko.error
    async def shikanoko_on_command_error(self, ctx: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.checks.CommandOnCooldown):
            retry_after_int = int(error.retry_after)
            retry_minute = retry_after_int // 60
            retry_second = retry_after_int % 60
            embed = discord.Embed(title="エラー",
                                  description=f"クールダウン中です。\nあと**{retry_minute}分{retry_second}秒**お待ちください。",
                                  color=0xff0000)
            embed.set_footer(text=f"Report ID: {ctx.id}")
            return await ctx.response.send_message(embed=embed, ephemeral=True)

    @shikanoko_ranking.error
    async def ranking_on_command_error(self, ctx: discord.Interaction, error: app_commands.AppCommandError):
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
    await bot.add_cog(Shikanoko(bot))

# Bot終了時にdb閉じておく
async def teardown(bot):
    bot.get_cog('Shikanoko').conn.close()