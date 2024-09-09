# 組み込みライブラリ
import secrets
import os
from datetime import datetime, timedelta, timezone
import re
import time
import random
import sqlite3
import asyncio

# 外部ライブラリ
import discord
from discord import app_commands
from discord.ext import commands  # Bot Commands Framework
import simplejson as json  # simplejson


##################################################

''' コマンド '''


class Money(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.money_db_connection
        self.c = self.conn.cursor()

        # ユーザー情報を保存するテーブルを作成
        self.c.execute('''
        CREATE TABLE IF NOT EXISTS user_data (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER,
            total_login INTEGER,
            last_login TIMESTAMP,
            last_work TIMESTAMP,
            transactions TEXT
        )
        ''')

        # transactionsテーブルの作成
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id TEXT PRIMARY KEY,
                from_user_id INTEGER,
                to_user_id INTEGER,
                amount INTEGER,
                tax INTEGER,
                datetime TIMESTAMP
            )
        ''')

        self.conn.commit()

    # Cog読み込み時

    @commands.Cog.listener()
    async def on_ready(self):
        print("MoneyCog on ready")

    #########################

    # /moneyコマンドをグループ化
    group = app_commands.Group(name="money", description="ウォレットのコマンド")

    # balance

    @group.command(name="balance", description="ウォレットの残高を表示します")
    @app_commands.checks.cooldown(2, 10)
    async def money_balance(self, ctx: discord.Interaction):
        # DBでuser_idが存在するか確認
        self.c.execute('SELECT balance, last_login FROM user_data WHERE user_id = ?', (ctx.user.id,))
        result = self.c.fetchone()

        # ウォレットを持っていれば表示
        if result:
            balance, last_login = result
            
            # last_loginをUTC+9してyyyy/mm/ddにしておく
            jst = timezone(timedelta(hours=9))
            last_login_dt = datetime.fromisoformat(last_login).astimezone(jst)
            formatted_last_login = last_login_dt.strftime('%Y/%m/%d %H:%M:%S')

            # usernameを更新
            self.c.execute('UPDATE user_data SET username = ? WHERE user_id = ?', (ctx.user.name, ctx.user.id))
            self.conn.commit()

            embed = discord.Embed(title=f"@{ctx.user.name} のウォレット",
                                  description=f"**残高**: {balance} ZNY",
                                  color=discord.Colour.green())
            embed.set_footer(text=f"最終ログイン: {formatted_last_login}")
            await ctx.response.send_message(embed=embed)

        else:
            # 持っていない
            embed = discord.Embed(title=":x: エラー",
                                  description=f"ウォレットが存在しません。\n`/money login`を実行してウォレットを開設してください。",
                                  color=0xff0000)
            await ctx.response.send_message(embed=embed, ephemeral=True)

    # login

    @group.command(name="login", description="マネーシステムにログインします")
    async def money_login(self, ctx: discord.Interaction):
        # DBでuser_idが存在するか確認
        self.c.execute('SELECT * FROM user_data WHERE user_id = ?', (ctx.user.id,))
        result = self.c.fetchone()

        now = datetime.now(timezone.utc) # 現在時刻(UTC)
        now_str = now.isoformat()

        # UTC+9
        jst = timezone(timedelta(hours=9))
        now_jst = now.astimezone(jst)
        formatted_now_jst = now_jst.strftime('%Y/%m/%d %H:%M:%S')

        # ウォレットを持っていればログイン、持っていなければ作成
        if result:
            balance, total_login, last_login = result[2], result[3], result[4]

            # UTC+9変換と翌日計算
            last_login_dt = datetime.fromisoformat(last_login).astimezone(jst)
            next_day = last_login_dt.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

            # 翌日以降かどうか
            if now_jst >= next_day:
                new_total_login = total_login + 1

                # 7日ボーナス
                if new_total_login % 7 == 0:
                    bonus = 5000

                else:
                    bonus = 1000

                self.c.execute('''
                    UPDATE user_data 
                    SET balance = ?, last_login = ?, total_login = ?, username = ?
                    WHERE user_id = ?
                ''', ((balance + bonus), now_str, new_total_login, ctx.user.name, ctx.user.id))
                self.conn.commit()

                embed = discord.Embed(title="ログインしました",
                                    description=f"**{bonus} ZNY**を受け取りました。現在の残高は**{balance + bonus} ZNY**です。",
                                    color=discord.Colour.green())
                embed.set_footer(text=f"通算ログイン日数: {new_total_login}日")
                await ctx.response.send_message(embed=embed)

            else:
                embed = discord.Embed(title=":x: エラー",
                                      description="今日は既にログインしています",
                                      color=0xff0000)
                await ctx.response.send_message(embed=embed, ephemeral=True)

        # 持っていなければ1000ZNY与えて作成
        else:
            # last_workを適当に設定
            last_str = (now - timedelta(hours=1)).isoformat()

            self.c.execute('''
                INSERT INTO user_data (user_id, username, balance, total_login, last_login, last_work, transactions)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (ctx.user.id, ctx.user.name, 1000, 1, now_str, last_str, '[]'))
            self.conn.commit()

            embed = discord.Embed(title=f"@{ctx.user.name} のウォレット",
                                  description="ウォレットを開設し、ボーナス**1000 ZNY**を受け取りました。\n**残高**: 1000 ZNY",
                                  color=discord.Colour.green())
            embed.set_footer(text=f"最終ログイン: {formatted_now_jst}")
            await ctx.response.send_message(embed=embed)

    # send

    @group.command(name="send", description="ユーザーに送金します（手数料5%）")
    @app_commands.describe(user="送金先ユーザーをメンションまたはユーザーIDで指定")
    @app_commands.describe(amount="送金金額を入力")
    async def money_send(self, ctx: discord.Interaction, user: str, amount: int):
        try:
            # メンションからID抽出
            target = re.sub("\\D", "", user)
            target_obj = await self.bot.fetch_user(target)

        except Exception:
            embed = discord.Embed(title=":x: エラー",
                                  description="ユーザーが見つかりませんでした",
                                  color=0xff0000)
            await ctx.followup.send(embed=embed, ephemeral=True)

        else:
            if target == str(ctx.user.id):
                embed = discord.Embed(title=":x: エラー",
                                      description="自分自身には送金できません",
                                      color=0xff0000)
                await ctx.followup.send(embed=embed, ephemeral=True)

            else:
                # DBから自分とターゲットユーザーの情報を取得
                self.c.execute('SELECT balance, transactions FROM user_data WHERE user_id = ?', (ctx.user.id,))
                sender_data = self.c.fetchone()
                self.c.execute('SELECT balance, transactions FROM user_data WHERE user_id = ?', (target,))
                target_data = self.c.fetchone()

                # 送金元ウォレットの存在確認
                if sender_data:
                    # 送金先ウォレットの存在確認
                    if target_data:
                        sender_balance, sender_transactions = sender_data
                        target_balance, target_transactions = target_data

                        now = datetime.now(timezone.utc) # 現在時刻(UTC)
                        now_str = now.isoformat()

                        # UTC+9
                        jst = timezone(timedelta(hours=9))
                        now_jst = now.astimezone(jst)
                        formatted_now_jst = now_jst.strftime('%Y/%m/%d %H:%M:%S')

                        if sender_balance >= amount and amount > 0:
                            transaction_time = time.time()
                            transaction_id = secrets.token_hex(10)

                            flag = False

                            # IDの生成を5回試行する
                            for i in range(5):
                                transaction_id = secrets.token_hex(10)

                                # 生成したIDが既に存在しないか確認
                                self.c.execute('SELECT 1 FROM transactions WHERE transaction_id = ?', (transaction_id,))

                                if not self.c.fetchone():
                                    flag = True
                                    break

                            else:
                                flag = False

                            if flag is True:
                                tax = int(amount * 0.05)

                                # transactionをDBに書き込み
                                self.c.execute('''
                                    INSERT INTO transactions (transaction_id, from_user_id, to_user_id, amount, tax, datetime)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                ''', (transaction_id, ctx.user.id, target, (amount - tax), tax, now_str))

                                sender_transactions = json.loads(sender_transactions)
                                sender_transactions.append(transaction_id)
                                target_transactions = json.loads(target_transactions)
                                target_transactions.append(transaction_id)

                                # データのセーブ
                                self.c.execute('''
                                    UPDATE user_data 
                                    SET balance = ?, transactions = ?, username = ?
                                    WHERE user_id = ?
                                ''', ((sender_balance - amount), json.dumps(sender_transactions), ctx.user.name, ctx.user.id))

                                self.c.execute('''
                                    UPDATE user_data 
                                    SET balance = ?, transactions = ?, username = ?
                                    WHERE user_id = ?
                                ''', ((target_balance + (amount - tax)), json.dumps(target_transactions), target_obj.name, target))

                                self.conn.commit()

                                embed = discord.Embed(title="送金完了",
                                                      description=f"**送金元**: @{ctx.user.name}\n"
                                                                  f"**送金先**: @{target_obj.name}\n"
                                                                  f"**送金額**: {amount - tax} ZNY (手数料: {tax} ZNY)\n"
                                                                  f"**トランザクションID**: {transaction_id}\n"
                                                                  f"**送金時刻**: {formatted_now_jst}",
                                                      color=discord.Colour.green())
                                await ctx.response.send_message(embed=embed)

                            else:
                                embed = discord.Embed(title=":x: エラー",
                                                      description="トランザクションIDの生成に失敗しました。再度お試しください。",
                                                      color=0xff0000)
                                await ctx.response.send_message(embed=embed, ephemeral=True)

                        else:
                            embed = discord.Embed(title=":x: エラー",
                                                  description="送金金額が不正です",
                                                  color=0xff0000)
                            await ctx.response.send_message(embed=embed, ephemeral=True)

                    else:
                        embed = discord.Embed(title=":x: エラー",
                                              description="そのユーザーはウォレットを開設していません",
                                            color=0xff0000)
                        await ctx.response.send_message(embed=embed, ephemeral=True)

                else:
                    embed = discord.Embed(title=":x: エラー",
                                          description="あなたはウォレットを開設していません",
                                          color=0xff0000)
                    await ctx.response.send_message(embed=embed, ephemeral=True)

    # work

    @app_commands.command(name="work", description="20分に1回働いてお金を貰えます")
    async def work(self, ctx: discord.Interaction):
        # DBでuser_idが存在するか確認
        self.c.execute('SELECT username, balance, last_work FROM user_data WHERE user_id = ?', (ctx.user.id,))
        result = self.c.fetchone()

        if result:
            previous = datetime.fromisoformat(result[2])
            now = datetime.now(timezone.utc)
            time_difference = now - previous # 秒数差計算
            seconds_difference = time_difference.total_seconds() # 秒数に直す

            if seconds_difference >= 1200:
                now_str = now.isoformat()

                works = [300, 400, 450, 500, 550, 600, 650, 700, 750, 800, 1000]
                salary = random.choice(works)
                self.c.execute('''
                    UPDATE user_data
                    SET balance = ?, last_work = ?, username = ?
                    WHERE user_id = ?
                ''', ((result[1] + salary), now_str, ctx.user.name, ctx.user.id))

                self.conn.commit()

                embed = discord.Embed(title=f"✅ {salary} ZNY獲得しました",
                                      description=f"現在の所持金: {result[1] + salary} ZNY",
                                      color=discord.Colour.green())
                await ctx.response.send_message(embed=embed)

            else:
                embed = discord.Embed(title=":x: エラー",
                                      description="前回の仕事から20分経過していません",
                                      color=0xff0000)
                await ctx.response.send_message(embed=embed, ephemeral=True)


        else:
            embed = discord.Embed(title=":x: エラー",
                                  description="あなたはウォレットを開設していません",
                                  color=0xff0000)
            await ctx.response.send_message(embed=embed, ephemeral=True)

    # slot

    @app_commands.command(name="slots", description="お金を賭けてスロットを回す")
    @app_commands.describe(amount="賭け金を入力")
    async def slots(self, ctx: discord.Interaction, amount: int):
        # DBでuser_idが存在するか確認
        self.c.execute('SELECT username, balance FROM user_data WHERE user_id = ?', (ctx.user.id,))
        result = self.c.fetchone()

        if result:
            if amount > 0 and result[1] >= amount:
                # メッセージ送信前に結果を確定する
                slots = [1, 2, 3, 4, 5, 6]
                odds = [4, 6, 8, 15, 30, 50]
                weights = [50, 30, 20, 15, 5, 1]
                emojis = ["<:slot1:1278510275976237056>", "<:slot2:1278510274437054484>", "<:slot3:1278510272222462034>",
                        "<:slot4:1278510270834282579>", "<:slot5:1278510269378723860>", "<:slot6:1278510267789082624>"]
                slot_result = random.choices(slots, k=3, weights=weights)
                bonus = (amount * -1)

                if len(set(slot_result)) == 1:
                    bonus = amount * (odds[slot_result[0] - 1] - 1)
                    wo = f"×{odds[slot_result[0] - 1]} WIN!"

                else:
                    wo = "LOSE..."


                # 先にお金の処理を終わらせる
                self.c.execute('''
                    UPDATE user_data
                    SET balance = ?
                    WHERE user_id = ?
                ''', (result[1] + bonus, ctx.user.id))

                self.conn.commit()

                try:
                    await ctx.response.send_message("**`___SLOTS___`**\n"
                    "`|`<a:slot_m1:1278511456412897310><a:slot_m2:1278511861842575460><a:slot_m3:1278512059872444509>`|`\n"
                    "`|         |`\n"
                    "`|_________|`\n"
                    f"**BET**: {amount} ZNY")

                    # 3回の編集を試みる
                    edits = [f"`|`{emojis[slot_result[0] - 1]}<a:slot_m2:1278511861842575460><a:slot_m3:1278512059872444509>`|`\n",
                            f"`|`{emojis[slot_result[0] - 1]}<a:slot_m2:1278511861842575460>{emojis[slot_result[2] - 1]}`|`\n",
                            f"`|`{emojis[slot_result[0] - 1]}{emojis[slot_result[1] - 1]}{emojis[slot_result[2] - 1]}`|`\n",]

                    for i in range(3):
                        await asyncio.sleep(0.2)

                        try:
                            content = "**`___SLOTS___`**\n" \
                                    + f"{edits[i]}" \
                                    + "`|         |`\n" \
                                    + "`|_________|`\n" \
                                    + f"**BET**: {amount} ZNY"

                            if i == 2:
                                content += f"\n**{wo}** ({bonus:+} ZNY)"

                            await ctx.edit_original_response(content=content)

                        except Exception:
                            break

                except Exception:
                    embed = discord.Embed(title=":x: エラー",
                                          description=f"不明なエラーが発生しました。\nスロット結果: {bonus:+} ZNY",
                                          color=0xff0000)
                    await ctx.response.send_message(embed=embed, ephemeral=True)

            else:
                embed = discord.Embed(title=":x: エラー",
                                      description="賭け金の値が不正です",
                                      color=0xff0000)
                await ctx.response.send_message(embed=embed, ephemeral=True)


        else:
            embed = discord.Embed(title=":x: エラー",
                                  description="あなたはウォレットを開設していません",
                                  color=0xff0000)
            await ctx.response.send_message(embed=embed, ephemeral=True)

    # coinflip

    @app_commands.command(name="coinflip", description="お金を賭けてコイントスする")
    @app_commands.describe(amount="賭け金を入力")
    async def coinflip(self, ctx: discord.Interaction, amount: int):
        # DBでuser_idが存在するか確認
        self.c.execute('SELECT username, balance FROM user_data WHERE user_id = ?', (ctx.user.id,))
        result = self.c.fetchone()

        if result:
            if amount > 0 and result[1] >= amount:
                # メッセージ送信前に結果を確定する
                emojis = ["<:cf_h:1278690322519560262>", "<:cf_t:1278690320472870972>"]
                cf_result = random.choice([True, False])
                bonus = (amount * -1)

                if cf_result is True:
                    bonus = amount
                    wo = f"WIN! ×2"
                    emoji = emojis[0]

                else:
                    wo = "LOSE..."
                    emoji = emojis[1]


                # 先にお金の処理を終わらせる
                self.c.execute('''
                    UPDATE user_data
                    SET balance = ?
                    WHERE user_id = ?
                ''', (result[1] + bonus, ctx.user.id))

                self.conn.commit()

                try:
                    await ctx.response.send_message("**`__コイントス__`**\n"
                        f"<a:coinflip:1278690240869044247> 抽選中...\n"
                        f"**BET**: {amount} ZNY")

                    # 編集を試みる
                    await asyncio.sleep(0.8)

                    try:
                        content = "**`__コイントス__`**\n" \
                                + f"{emoji} **{wo}** ({bonus:+} ZNY)\n" \
                                + f"**BET**: {amount} ZNY"

                        await ctx.edit_original_response(content=content)

                    except Exception:
                        pass

                except Exception:
                    embed = discord.Embed(title=":x: エラー",
                                          description=f"不明なエラーが発生しました。\n結果: {bonus:+} ZNY",
                                          color=0xff0000)
                    await ctx.response.send_message(embed=embed, ephemeral=True)

            else:
                embed = discord.Embed(title=":x: エラー",
                                      description="賭け金の値が不正です",
                                      color=0xff0000)
                await ctx.response.send_message(embed=embed, ephemeral=True)


        else:
            embed = discord.Embed(title=":x: エラー",
                                  description="あなたはウォレットを開設していません",
                                  color=0xff0000)
            await ctx.response.send_message(embed=embed, ephemeral=True)

    # ranking

    @group.command(name="ranking", description="長者番付")
    async def ranking(self, ctx: discord.Interaction):
        # データ読み込み

        # トップ10のユーザーを取得
        self.c.execute('''
        SELECT user_id, balance FROM user_data
        ORDER BY balance DESC
        LIMIT 10
        ''')
        top10_rows = self.c.fetchall()

        top10_users = []
        rank = 1
        previous_balance = None
        current_rank = 1

        # トップ10のユーザーの順位を決定
        for id, balance in top10_rows:
            # データベースから最新のユーザー名を取得
            self.c.execute('SELECT username FROM user_data WHERE user_id = ?', (id,))
            username = self.c.fetchone()[0]

            # 順位の重複処理
            if previous_balance is None or balance < previous_balance:
                current_rank = rank

            rank += 1
            previous_balance = balance

            top10_users.append(f"{current_rank}位: `@{username}`  **{balance} ZNY**")

        # 自分の順位を取得
        self.c.execute('''
        SELECT COUNT(*) + 1 FROM user_data
        WHERE balance > (SELECT balance FROM user_data WHERE user_id = ?)
        ''', (ctx.user.id,))
        user_rank = self.c.fetchone()[0]

        # 自分のあたり回数を取得
        self.c.execute('SELECT balance FROM user_data WHERE user_id = ?', (ctx.user.id,))
        user_balance = self.c.fetchone()

        # 自分の順位とあたり回数を表示
        if user_balance:
            user_rank_data = f"{user_rank}位: `@{ctx.user.name}`  **{user_balance[0]} ZNY**"

        else:
            user_rank_data = "集計対象外"

        # embedデータの作成
        desc = "**[所持金TOP10]**\n"

        for i in top10_users:
            desc += f"{i}\n"

        desc += f"\n**[あなたの順位]**\n{user_rank_data}"

        # 現在時刻
        now = datetime.now(timezone.utc) # 現在時刻(UTC)

        # UTC+9
        jst = timezone(timedelta(hours=9))
        now_jst = now.astimezone(jst)
        formatted_now_jst = now_jst.strftime('%Y/%m/%d %H:%M:%S')

        embed = discord.Embed(title="長者番付",
                            description=desc,
                            color=discord.Colour.green())
        embed.set_footer(text=f"ランキング取得時刻: {formatted_now_jst}")
        await ctx.response.send_message(embed=embed)

    # give

    @commands.command()
    @commands.is_owner()
    async def give(self, ctx: discord.Interaction, userid: int, val: int):
        # DBでuser_idが存在するか確認
        self.c.execute('SELECT balance FROM user_data WHERE user_id = ?', (userid,))
        result = self.c.fetchone()

        if result:
            new_balance = result[0] + val

            if new_balance < 0:
                new_balance = 0

            self.c.execute('''
                UPDATE user_data
                SET balance = ?
                WHERE user_id = ?
            ''', (new_balance, userid))

            self.conn.commit()

            await ctx.reply(f":white_check_mark: `{userid}`に**{val} ZNY**与えました", mention_author=False)

        else:
            await ctx.reply(":x: そのユーザーのウォレットは作成されていません", mention_author=False)

    #########################

    ''' クールダウン '''

    @money_balance.error
    async def money_balance_on_command_error(self, ctx: discord.Interaction, error: app_commands.AppCommandError):
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
    await bot.add_cog(Money(bot))

# Bot終了時にdb閉じておく
async def teardown(bot):
    bot.get_cog('Money').conn.close()