# 組み込みライブラリ
import secrets
from datetime import datetime, timedelta, timezone
import re
import random
import sqlite3
import asyncio

# 外部ライブラリ
import discord
from discord import app_commands
from discord.ext import commands  # Bot Commands Framework
import simplejson as json  # simplejson


##################################################

SEND_TAX = 0.10  # 送金手数料

##################################################

def get_level_from_experience(total_experience):
    """
    総獲得経験値に基づいてレベルを計算する関数
    経験値は指数的に増加する。
    """
    base_xp = 100  # レベル1→2に必要な経験値
    growth_factor = 1.5  # 経験値増加の指数係数
    
    level = 1  # レベル1からスタート
    required_xp = base_xp
    
    # 経験値がレベルアップに達するまで繰り返し
    while total_experience >= required_xp:
        total_experience -= required_xp
        level += 1
        required_xp = int(base_xp * (level ** growth_factor))

    # レベル上限
    if level > 100:
        level = 100
    
    return level


def get_next_level_experience(total_experience):
    """
    現在の総獲得経験値に基づいて次のレベルに到達するために必要な経験値を計算する関数
    """
    base_xp = 100  # レベル1→2に必要な経験値
    growth_factor = 1.5  # 経験値増加の指数係数

    level = 1  # レベル1からスタート
    required_xp = base_xp

    # 現在のレベルを計算
    while total_experience >= required_xp:
        total_experience -= required_xp
        level += 1
        required_xp = int(base_xp * (level ** growth_factor))

    # レベル100でストップ
    if level >= 100:
        return 0

    # 次のレベルに必要な経験値
    next_level_experience = required_xp - total_experience
    return next_level_experience

##################################################

''' コマンド '''


class Money(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.money_db_connection
        self.c = self.conn.cursor()
        self.conn_settings = bot.settings_db_connection
        self.c_settings = self.conn_settings.cursor()

        # ユーザー情報を保存するテーブルを作成
        self.c.execute('''
        CREATE TABLE IF NOT EXISTS user_data (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER,
            badges TXT,
            exp INT,
            level INT,
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

    @group.command(name="balance", description="所持金を表示します")
    @app_commands.checks.cooldown(2, 10)
    async def money_balance(self, ctx: discord.Interaction):
        # DBでuser_idが存在するか確認
        self.c.execute('SELECT balance, last_login FROM user_data WHERE user_id = ?', (ctx.user.id,))
        result = self.c.fetchone()

        # ephemeral #
        self.c_settings.execute('SELECT ephemeral FROM user_settings WHERE user_id = ?', (ctx.user.id,))
        user_setting = self.c_settings.fetchone()

        if user_setting:
            ephemeral = True if user_setting[0] == 1 else False

        else:
            ephemeral = 0

        #####

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
                                  description=f"**所持金**: {balance:,} ZNY",
                                  color=discord.Colour.green())
            embed.set_footer(text=f"最終ログイン: {formatted_last_login}")
            await ctx.response.send_message(embed=embed, ephemeral=ephemeral)

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
        self.c.execute('SELECT balance, exp, level, total_login, last_login FROM user_data WHERE user_id = ?', (ctx.user.id,))
        result = self.c.fetchone()

        # ephemeral #
        self.c_settings.execute('SELECT ephemeral FROM user_settings WHERE user_id = ?', (ctx.user.id,))
        user_setting = self.c_settings.fetchone()

        if user_setting:
            ephemeral = True if user_setting[0] == 1 else False

        else:
            ephemeral = 0

        #####

        now = datetime.now(timezone.utc) # 現在時刻(UTC)
        now_str = now.isoformat()

        # UTC+9
        jst = timezone(timedelta(hours=9))
        now_jst = now.astimezone(jst)
        formatted_now_jst = now_jst.strftime('%Y/%m/%d %H:%M:%S')

        # ウォレットを持っていればログイン、持っていなければ作成
        if result:
            balance, exp, level, total_login, last_login = result[0], result[1], result[2], result[3], result[4]

            # UTC+9変換と翌日計算
            last_login_dt = datetime.fromisoformat(last_login).astimezone(jst)
            next_day = last_login_dt.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

            # 翌日以降かどうか
            if now_jst >= next_day:
                new_total_login = total_login + 1

                # 7日ボーナス
                if new_total_login % 7 == 0:
                    bonus = 5000
                    exp_bonus = 1250

                    # 試験中 レベルブースト
                    bonus += int(bonus * (level - 1) * 0.05)
                    exp_bonus += int(exp_bonus * (level - 1) * 0.1)

                else:
                    bonus = 1000
                    exp_bonus = 250

                    # 試験中 レベルブースト
                    bonus += int(bonus * (level - 1) * 0.05)
                    exp_bonus += int(exp_bonus * (level - 1) * 0.1)

                self.c.execute('''
                    UPDATE user_data 
                    SET balance = ?, badges = ?, exp = ?, last_login = ?, total_login = ?, username = ?
                    WHERE user_id = ?
                ''', ((balance + bonus), "", (exp + exp_bonus), now_str, new_total_login, ctx.user.name, ctx.user.id))
                self.conn.commit()

                # 新しいレベルを計算
                new_level = get_level_from_experience(exp + exp_bonus)

                # レベルが上がった場合のみレベルを更新
                if new_level != level:
                    self.c.execute("UPDATE user_data SET level = ? WHERE user_id = ?", 
                            (new_level, ctx.user.id))
                    self.conn.commit()

                    embed = discord.Embed(title="ログインしました",
                                          description=f"**{bonus:,} ZNY**を獲得しました。 (+{exp_bonus:,} XP)\n所持金: {balance + bonus:,} ZNY\n**[レベルアップ！ (Lv.{result[2]}→Lv.{new_level})]**",
                                          color=discord.Colour.green())

                else:
                    embed = discord.Embed(title="ログインしました",
                                          description=f"**{bonus:,} ZNY**を獲得しました。 (+{exp_bonus:,} XP)\n所持金: {balance + bonus:,} ZNY",
                                          color=discord.Colour.green())

                embed.set_footer(text=f"通算ログイン日数: {new_total_login}日")
                await ctx.response.send_message(embed=embed, ephemeral=ephemeral)

            else:
                next_day_unix = int(next_day.timestamp()) # UNIX時間に変換

                embed = discord.Embed(title=":x: エラー",
                                      description=f"今日は既にログインしています。\n<t:{next_day_unix}:f>以降にお試しください。",
                                      color=0xff0000)
                await ctx.response.send_message(embed=embed, ephemeral=True)

        # 持っていなければ1000ZNY与えて作成
        else:
            # last_workを適当に設定
            last_str = (now - timedelta(hours=1))

            self.c.execute('''
                INSERT INTO user_data (user_id, username, balance, badges, exp, level, total_login, last_login, last_work, transactions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (ctx.user.id, ctx.user.name, 1000, "", 0, 1, 1, now_str, last_str, '[]'))
            self.conn.commit()

            embed = discord.Embed(title=f"@{ctx.user.name} のウォレット",
                                  description="ウォレットを開設し、ボーナス**1,000 ZNY**を受け取りました。\n所持金: 1,000 ZNY",
                                  color=discord.Colour.green())
            embed.set_footer(text=f"最終ログイン: {formatted_now_jst}")
            await ctx.response.send_message(embed=embed, ephemeral=ephemeral)

    # send

    @group.command(name="send", description="ユーザーに送金します（手数料10%）")
    @app_commands.describe(user="送金先ユーザーをメンションまたはユーザーIDで指定")
    @app_commands.describe(amount="送金金額を入力")
    async def money_send(self, ctx: discord.Interaction, user: str, amount: int):
        # ephemeral #
        self.c_settings.execute('SELECT ephemeral FROM user_settings WHERE user_id = ?', (ctx.user.id,))
        user_setting = self.c_settings.fetchone()

        if user_setting:
            ephemeral = True if user_setting[0] == 1 else False

        else:
            ephemeral = 0

        #####

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

                        # 所持金の範囲かつ100 ZNY以上
                        if sender_balance >= amount and amount >= 100:
                            transaction_time = datetime.utcnow().timestamp() # 現在時刻(UNIX)

                            # 時間変換
                            td = 9 # UTC+9
                            time_difference = timezone(timedelta(hours=td))
                            formatted_transaction_time = datetime.fromtimestamp(transaction_time, time_difference).strftime("%Y/%m/%d %H:%M:%S")

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
                                tax = int(amount * SEND_TAX) # 手数料

                                # transactionをDBに書き込み
                                self.c.execute('''
                                    INSERT INTO transactions (transaction_id, from_user_id, to_user_id, amount, tax, datetime)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                ''', (transaction_id, ctx.user.id, target, (amount - tax), tax, transaction_time))

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
                                                      description=f"**送金元**: `@{ctx.user.name}`\n"
                                                                  f"**送金先**: `@{target_obj.name}`\n"
                                                                  f"**送金額**: {amount - tax:,} ZNY (手数料: {tax:,} ZNY)\n"
                                                                  f"**トランザクションID**: {transaction_id}\n"
                                                                  f"**送金時刻**: {formatted_transaction_time} (UTC+{td})",
                                                      color=discord.Colour.green())
                                await ctx.response.send_message(embed=embed, ephemeral=ephemeral)

                            else:
                                embed = discord.Embed(title=":x: エラー",
                                                      description="トランザクションIDの生成に失敗しました。再度お試しください。",
                                                      color=0xff0000)
                                await ctx.response.send_message(embed=embed, ephemeral=True)

                        else:
                            embed = discord.Embed(title=":x: エラー",
                                                  description="送金金額が不正または100 ZNY未満です",
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
        self.c.execute('SELECT username, balance, exp, level, last_work FROM user_data WHERE user_id = ?', (ctx.user.id,))
        result = self.c.fetchone()

        # ephemeral #
        self.c_settings.execute('SELECT ephemeral FROM user_settings WHERE user_id = ?', (ctx.user.id,))
        user_setting = self.c_settings.fetchone()

        if user_setting:
            ephemeral = True if user_setting[0] == 1 else False

        else:
            ephemeral = 0

        #####

        if result:
            previous = datetime.fromisoformat(result[4])
            now = datetime.now(timezone.utc)
            time_difference = now - previous # 秒数差計算
            seconds_difference = time_difference.total_seconds() # 秒数に直す

            if seconds_difference >= 1200:
                now_str = now.isoformat()

                works = [300, 400, 450, 500, 550, 600, 650, 700, 750, 800, 1000]
                xps = [100, 150, 175, 200, 225, 250]
                salary = random.choice(works)
                gain_xp = random.choice(xps)

                # 試験中 レベルブースト
                salary += int(salary * (result[3] - 1) * 0.05)
                gain_xp += int(gain_xp * (result[3] - 1) * 0.1)

                self.c.execute('''
                    UPDATE user_data
                    SET balance = ?, exp = ?, last_work = ?, username = ?
                    WHERE user_id = ?
                ''', ((result[1] + salary), (result[2] + gain_xp), now_str, ctx.user.name, ctx.user.id))

                self.conn.commit()

                # 新しいレベルを計算
                new_level = get_level_from_experience(result[2] + gain_xp)

                # レベルが上がった場合のみレベルを更新
                if new_level != result[3]:
                    self.c.execute("UPDATE user_data SET level = ? WHERE user_id = ?", 
                            (new_level, ctx.user.id))
                    self.conn.commit()

                    embed = discord.Embed(title=f"✅ {salary:,} ZNY獲得しました (+{gain_xp:,} XP)",
                                        description=f"所持金: {result[1] + salary:,} ZNY\n**[レベルアップ！ (Lv.{result[3]}→Lv.{new_level})]**",
                                        color=discord.Colour.green())

                else:
                    embed = discord.Embed(title=f"✅ {salary:,} ZNY獲得しました (+{gain_xp:,} XP)",
                                        description=f"所持金: {result[1] + salary:,} ZNY",
                                        color=discord.Colour.green())
                
                await ctx.response.send_message(embed=embed, ephemeral=ephemeral)

            else:
                embed = discord.Embed(title=":x: エラー",
                                    description=f"前回の仕事から20分経過していません。\n<t:{int(previous.timestamp()) + 1200}:R>にお試しください。",
                                    color=0xff0000)
                await ctx.response.send_message(embed=embed, ephemeral=True)


        else:
            embed = discord.Embed(title=":x: エラー",
                                description="あなたはウォレットを開設していません",
                                color=0xff0000)
            await ctx.response.send_message(embed=embed, ephemeral=True)

    # slots

    @app_commands.command(name="slots", description="お金を賭けてスロットを回す")
    @app_commands.describe(amount="賭け金を入力")
    async def slots(self, ctx: discord.Interaction, amount: int):
        # DBでuser_idが存在するか確認
        self.c.execute('SELECT username, balance FROM user_data WHERE user_id = ?', (ctx.user.id,))
        result = self.c.fetchone()
        balance = result[1]

        # ephemeral #
        self.c_settings.execute('SELECT ephemeral FROM user_settings WHERE user_id = ?', (ctx.user.id,))
        user_setting = self.c_settings.fetchone()

        if user_setting:
            ephemeral = True if user_setting[0] == 1 else False

        else:
            ephemeral = False

        #####

        if result:
            if amount > 0 and result[1] >= amount and amount <= 200000:
                # メッセージ送信前に結果を確定する
                slots = [1, 2, 3, 4, 5, 6]
                odds = [4.0, 6.0, 8.0, 15, 30, 50]
                weights = [50, 30, 20, 15, 5, 1]
                emojis = ["<:SLOT_1:1310233464888360981>", "<:SLOT_2:1310233480583577660>", "<:SLOT_3:1310233497696342210>",
                        "<:SLOT_4:1310233526771384440>", "<:SLOT_5:1310233545909993502>", "<:SLOT_6:1310233563567886356>"]
                slot_result = random.choices(slots, k=3, weights=weights)
                bonus = (amount * -1)

                if len(set(slot_result)) == 1:
                    bonus = int(amount * (odds[slot_result[0] - 1] - 1))
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
                    "`|`<a:SLOT_M1:1310233252950446112><a:SLOT_M2:1310233262274117642><a:SLOT_M3:1310233271392534550>`|`\n"
                    "`|         |`\n"
                    "`|_________|`\n"
                    f"**BET**: {amount:,} ZNY\n"
                    f"**所持金**: {balance:,} ZNY", ephemeral=ephemeral)

                    # 3回の編集を試みる
                    edits = [f"`|`{emojis[slot_result[0] - 1]}<a:SLOT_M2:1310233262274117642><a:SLOT_M3:1310233271392534550>`|`\n",
                            f"`|`{emojis[slot_result[0] - 1]}<a:SLOT_M2:1310233262274117642>{emojis[slot_result[2] - 1]}`|`\n",
                            f"`|`{emojis[slot_result[0] - 1]}{emojis[slot_result[1] - 1]}{emojis[slot_result[2] - 1]}`|`\n",]

                    for i in range(3):
                        await asyncio.sleep(0.2)

                        try:
                            content = "**`___SLOTS___`**\n" \
                                    + f"{edits[i]}" \
                                    + "`|         |`\n" \
                                    + "`|_________|`\n" \
                                    + f"**BET**: {amount:,} ZNY\n" \
                                    + f"**所持金**: {balance:,} ZNY"

                            if i == 2:
                                content = "**`___SLOTS___`**\n" \
                                    + f"{edits[2]}" \
                                    + "`|         |`\n" \
                                    + "`|_________|`\n" \
                                    + f"**{wo}** ({int(bonus):+,} ZNY)\n" \
                                    + f"**BET**: {amount:,} ZNY\n" \
                                    + f"**所持金**: {(result[1] + bonus):,} ZNY"

                            await ctx.edit_original_response(content=content)

                        except Exception:
                            break

                except Exception:
                    embed = discord.Embed(title=":x: エラー",
                                          description=f"不明なエラーが発生しましたが、スロットは正常に終了しました。\nスロット結果: {bonus:+,} ZNY",
                                          color=0xff0000)
                    await ctx.response.send_message(embed=embed, ephemeral=True)

            else:
                embed = discord.Embed(title=":x: エラー",
                                      description=f"残高不足または賭け金が正しくありません。\n賭け金は1～200,000 ZNYである必要があります。\n所持金: {result[1]:,} ZNY",
                                      color=0xff0000)
                await ctx.response.send_message(embed=embed, ephemeral=True)


        else:
            embed = discord.Embed(title=":x: エラー",
                                  description="あなたはまだウォレットを開設していません。\n`/money login`を実行して開設してください。",
                                  color=0xff0000)
            await ctx.response.send_message(embed=embed, ephemeral=True)

    # coinflip

    @app_commands.command(name="coinflip", description="お金を賭けてコイントスする")
    @app_commands.describe(amount="賭け金を入力")
    async def coinflip(self, ctx: discord.Interaction, amount: int):
        # DBでuser_idが存在するか確認
        self.c.execute('SELECT username, balance FROM user_data WHERE user_id = ?', (ctx.user.id,))
        result = self.c.fetchone()

        # ephemeral #
        self.c_settings.execute('SELECT ephemeral FROM user_settings WHERE user_id = ?', (ctx.user.id,))
        user_setting = self.c_settings.fetchone()

        if user_setting:
            ephemeral = True if user_setting[0] == 1 else False

        else:
            ephemeral = False

        #####

        if result:
            if amount > 0 and result[1] >= amount and amount <= 30000:
                # メッセージ送信前に結果を確定する
                emojis = ["<:COIN_FRONT:1310228758246195220>", "<:COIN_BACK:1310228896079151184>"]
                cf_result = random.choice([True, False])
                bonus = (amount * -1)

                if cf_result is True:
                    bonus = amount
                    wo = f"WIN! ×2.0"
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
                        f"<a:COINFLIP:1310231581960437760> 抽選中...\n"
                        f"**BET**: {amount:,} ZNY\n"
                        f"**所持金**: {result[1]:,} ZNY", ephemeral=ephemeral)

                    # 編集を試みる
                    await asyncio.sleep(0.8)

                    try:
                        content = "**`__コイントス__`**\n" \
                                + f"{emoji} **{wo}** ({bonus:+,} ZNY)\n" \
                                + f"**BET**: {amount:,} ZNY\n" \
                                + f"**所持金**: {(result[1] + bonus):,} ZNY"

                        await ctx.edit_original_response(content=content)

                    except Exception:
                        pass

                except Exception:
                    embed = discord.Embed(title=":x: エラー",
                                          description=f"不明なエラーが発生しました。\n結果: {bonus:+,} ZNY",
                                          color=0xff0000)
                    await ctx.response.send_message(embed=embed, ephemeral=True)

            else:
                embed = discord.Embed(title=":x: エラー",
                                      description=f"残高不足または賭け金が正しくありません。\n賭け金は1～30,000 ZNYである必要があります。\n現在の所持金: {result[1]:,} ZNY",
                                      color=0xff0000)
                await ctx.response.send_message(embed=embed, ephemeral=True)


        else:
            embed = discord.Embed(title=":x: エラー",
                                  description="あなたはウォレットを開設していません。\n`/money login`を実行して開設してください。",
                                  color=0xff0000)
            await ctx.response.send_message(embed=embed, ephemeral=True)

    # profile

    @app_commands.command(name="profile", description="プロフィールを確認する")
    @app_commands.describe(user="ユーザーをメンションまたはユーザーIDで指定")
    async def profile(self, ctx: discord.Interaction, user: str = None):
        # ephemeral #
        self.c_settings.execute('SELECT ephemeral FROM user_settings WHERE user_id = ?', (ctx.user.id,))
        user_setting = self.c_settings.fetchone()

        if user_setting:
            ephemeral = True if user_setting[0] == 1 else False

        else:
            ephemeral = False

        #####

        if user:
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
            user = await self.bot.fetch_user(ctx.user.id)
            target = ctx.user.id

        embed = discord.Embed(title="プロフィール",
                              description="",
                              color=discord.Colour.green())

        # アイコンが設定できるならしておく
        if hasattr(user.avatar, 'key'):
            embed.set_thumbnail(url=user.avatar.url)

        # DBでuser_idが存在するか確認
        self.c.execute('SELECT balance, badges, exp, total_login FROM user_data WHERE user_id = ?', (target,))
        result = self.c.fetchone()
        
        if result:
            balance = f"{result[0]:,} ZNY"
            badges = result[1]
            exp = result[2]
            total = result[3]
            level = get_level_from_experience(exp)
            next_xp = get_next_level_experience(exp)

            if len(badges) == 0:
                badges = "なし"
        
        else:
            balance = "(ウォレット未開設)"
            badges = "なし"
            exp = 0
            total = 0

        # DBでuser_idが存在するか確認
        self.c_settings.execute('SELECT spotify_time, spotify_total_time FROM user_settings WHERE user_id = ?', (target,))
        settings_result = self.c_settings.fetchone()

        if settings_result:
            if settings_result[0] == True:
                spotify_time = settings_result[1]

            else:
                spotify_time = 0

        else:
            spotify_time = 0

        # Bot判定
        if str(user.discriminator) != "0":
            # Akane判定
            if user.id == 777557090562474044:
                embed.add_field(name=f"{user.name}#{user.discriminator} [SYSTEM]", value=f"**総経験値**: 3,950,079 XP", inline=False)
                embed.add_field(name="バッジ", value="🛠️🤖", inline=True)
                embed.add_field(name="ステータス", value=f"このユーザーはシステムBOTです", inline=True)

            else:
                embed.add_field(name=f"{user.name}#{user.discriminator} [BOT]", value=f"**総経験値**: 0 XP", inline=False)
                embed.add_field(name="バッジ", value="🤖", inline=True)
                embed.add_field(name="ステータス", value=f"このユーザーはBOTです", inline=True)

        else:
            if level == 100:
                embed.add_field(name=f"@{user.name} [Lv.{level}]", value=f"**最大レベル到達**\n**総経験値**: {exp:,} XP", inline=False)

            else:
                embed.add_field(name=f"@{user.name} [Lv.{level}]", value=f"あと **{next_xp:,} XP** で **Lv.{min(level + 1, 100)}**\n**総経験値**: {exp:,} XP", inline=False)

            embed.add_field(name="バッジ", value=badges, inline=True)
            embed.add_field(name="ステータス", value=f"**所持金**: {balance}\n**通算ログイン日数**: {total}日\n**Spotify再生時間**: {spotify_time:,}分", inline=True)

        await ctx.response.send_message(embed=embed ,ephemeral=ephemeral)



    # ranking

    @group.command(name="ranking", description="長者番付")
    async def ranking(self, ctx: discord.Interaction):
        # データ読み込み

        # ephemeral #
        self.c_settings.execute('SELECT ephemeral FROM user_settings WHERE user_id = ?', (ctx.user.id,))
        user_setting = self.c_settings.fetchone()

        if user_setting:
            ephemeral = True if user_setting[0] == 1 else False

        else:
            ephemeral = False

        #####

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

            top10_users.append(f"{current_rank}位: `@{username}`  **{balance:,} ZNY**")

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
            user_rank_data = f"{user_rank}位: `@{ctx.user.name}`  **{user_balance[0]:,} ZNY**"

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
        await ctx.response.send_message(embed=embed, ephemeral=ephemeral)

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

            await ctx.reply(f":white_check_mark: `{userid}`に**{val:,} ZNY**与えました", mention_author=False)

        else:
            await ctx.reply(":x: そのユーザーのウォレットは作成されていません", mention_author=False)

    # givexp

    @commands.command()
    @commands.is_owner()
    async def givexp(self, ctx: discord.Interaction, userid: int, val: int):
        # DBでuser_idが存在するか確認
        self.c.execute('SELECT exp, level FROM user_data WHERE user_id = ?', (userid,))
        result = self.c.fetchone()

        if result:
            new_exp = result[0] + val

            if new_exp < 0:
                new_exp = 0

            level = get_level_from_experience(new_exp)

            self.c.execute('''
                UPDATE user_data
                SET exp = ?, level = ?
                WHERE user_id = ?
            ''', (new_exp, level, userid))

            self.conn.commit()

            await ctx.reply(f":white_check_mark: `{userid}`に**{val:,} XP**与えました (Lv.{result[1]}→Lv.{level})", mention_author=False)

        else:
            await ctx.reply(":x: そのユーザーのウォレットは作成されていません", mention_author=False)

    # resetwork

    @commands.command()
    @commands.is_owner()
    async def resetwork(self, ctx: discord.Interaction, userid: int):
        # DBでuser_idが存在するか確認
        self.c.execute('SELECT last_work FROM user_data WHERE user_id = ?', (userid,))
        result = self.c.fetchone()

        if result:
            # 最終workを適当に設定
            last_str = datetime(2000, 1, 1, 0, 0, tzinfo=timezone.utc).isoformat()

            self.c.execute('''
                UPDATE user_data
                SET last_work = ?
                WHERE user_id = ?
            ''', (last_str, userid))

            self.conn.commit()

            await ctx.reply(f":white_check_mark: `{userid}`のworkをリセットしました", mention_author=False)

        else:
            await ctx.reply(":x: そのユーザーのウォレットは作成されていません", mention_author=False)

    # resetlogin

    @commands.command()
    @commands.is_owner()
    async def resetlogin(self, ctx: discord.Interaction, userid: int):
        # DBでuser_idが存在するか確認
        self.c.execute('SELECT last_login FROM user_data WHERE user_id = ?', (userid,))
        result = self.c.fetchone()

        if result:
            # 最終workを適当に設定
            last_str = datetime(2000, 1, 1, 0, 0, tzinfo=timezone.utc).isoformat()

            self.c.execute('''
                UPDATE user_data
                SET last_login = ?
                WHERE user_id = ?
            ''', (last_str, userid))

            self.conn.commit()

            await ctx.reply(f":white_check_mark: `{userid}`のloginをリセットしました", mention_author=False)

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