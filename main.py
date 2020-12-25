#インポート群
import discord #基本
import os
from server import keep_alive
#import traceback
import random #さいころ
from googlesearch import search #画像検索
import time #Ping
#from lib import uranai #占い

#変数群
TOKEN = os.getenv("TOKEN") #トークン
prefix = 't.' #Prefix
activity = discord.Streaming(name='t.help でヘルプ♪', url="https://www.twitch.tv/discord")
embed_help = discord.Embed(title="Kotoha コマンドリスト",description="※現在は仮運用中です\nt.neko…にゃーん\nt.dice…サイコロを振るよ\nt.kuji…おみくじをひくよ\nt.search…Googleで検索をするよ（上位3件）\nt.janken…じゃんけんをするよ\nt.ping…BotのPingを取得するよ\nt.kick <ユーザー名>…キックを実行するよ\nt.ban <ユーザー名>…BANを実行するよ\n\n（このBotは半自動です。たまに人が会話します）")
ModeFlag = 0 #Google検索モードオフ

#接続に必要なオブジェクトを生成
client = discord.Client()

#起動時に動作する処理
@client.event
async def on_ready():
    # 起動したらターミナルにログイン通知が表示される
    print('[Kotoha] ログインしました')
    await client.change_presence(activity=activity)

#メッセージ受信時に動作する処理
@client.event
async def on_message(message):
  global ModeFlag, result, judge
  if message.author.bot:
    return
  if message.content == prefix + 'help':
    await message.channel.send(embed=embed_help)
        
    #にゃーん
  if message.content == prefix + 'neko':
    await message.channel.send('にゃーん')
        
    #Ping
  if message.content == prefix + 'ping':
    time_then = time.monotonic()
    ping_send = await message.channel.send('__*`Pingを取得中...`*__')
    ping = '%.2f' % (1000*(time.monotonic()-time_then))
    await ping_send.edit(content='**Ping: **' + ping + 'ms')

    #Dice
  if message.content == prefix + 'dice':
    word_list = [":one:",":two:",":three:",":four:",":five:",":six:"]
    await message.channel.send(random.choice(word_list) + 'が出たよ')
    
    #Kick
  if message.content.startswith(prefix + 'kick'):
    try:
      args = message.content.split()
      user = discord.utils.get(message.guild.members, name=args[1])
      await user.kick()
      embed=discord.Embed(title="キックが正常に実行されました", color=0xff0000)
      embed.set_thumbnail(url=user.avatar_url)
      embed.add_field(name="対象", value=user, inline=False)
      embed.add_field(name="実行", value=message.author, inline=False)
      await message.channel.send(embed=embed)
    except:
      await message.channel.send('**エラーが発生しました。**ユーザー名は名前のみで指定してください')
        
        
    #Ban
  if message.content.startswith(prefix + 'ban'):
    try:
      args = message.content.split()
      user = discord.utils.get(message.guild.members, name=args[1])
      await user.ban()
      embed=discord.Embed(title="BANが正常に実行されました", color=0xff0000)
      embed.set_thumbnail(url=user.avatar_url)
      embed.add_field(name="対象", value=user, inline=False)
      embed.add_field(name="実行", value=message.author, inline=False)
      await message.channel.send(embed=embed)
    except:
      await message.channel.send('**エラーが発生しました。**ユーザー名は名前のみで指定してください')
        
    '''
    #UnBan
    if message.content.startswith(prefix + 'unban'):
        args = message.content.split()
        user = discord.utils.find(lambda banentry: args[1] == banentry.user.name, await message.guild.bans()).user
        await user.unban()
        embed=discord.Embed(title="BANを解除しました", color=0xff0000)
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name="対象", value=user, inline=False)
        embed.add_field(name="実行", value=message.author, inline=False)
        await message.channel.send(embed=embed)
    '''
    
    #占い
  if message.content == prefix + 'kuji':
    omikuji_list = ["大大凶", "大凶", "凶", "末吉", "小吉", "中吉", "吉", "大吉", "大大吉"]
    await message.channel.send('今日の運勢は...** ' + random.choice(omikuji_list) + '**だよ！')
        
    #Google検索
  if ModeFlag == 1:
    kensaku = message.content
    ModeFlag = 0
    count = 0
    searched = []
    search_send = await message.channel.send('**検索中...**')
    #日本語で検索した上位3件を順番に表示
    for url in search(kensaku, lang="jp",num = 3):
        searched.append(url)
        count += 1
        if(count == 3):
            try:
              await search_send.delete()
            except:
              pass
              embed = discord.Embed(title="検索結果",description=":one: " + searched[0] + "\n:two: " + searched[1] + "\n:three: " + searched[2])
              await message.channel.send(embed=embed)
              break
            
  #Google検索モードへの切り替え
  if message.content == prefix + 'search':
    ModeFlag = 1
    try:
      search_wait_send = await message.channel.send('検索したい言葉を送信してね')
      await client.wait_for('search_wait', timeout=20)
    except:
      ModeFlag = 0
      await search_wait_send.edit(content='**タイムオーバーしました。**\n検索したいときはもう一度コマンドを入力してね')
        
  if message.content == prefix + 'janken':
    await message.channel.send("最初はぐー、じゃんけん（ぐー・ちょき・ぱーのどれかで送信してね）")

    jkbot = random.choice(("ぐー", "ちょき", "ぱー"))
    draw = "私は" + jkbot + "。" + "引き分けだよ～"
    wn = "私は" + jkbot + "。" + "君の勝ち！"
    lst = random.choice(("私は" + jkbot + "。" + "私の勝ち！やったぁ","私は" + jkbot + "。" + "私の勝ちだね(∩´∀｀)∩、また挑戦してね！"))

    def jankencheck(m):
      return (m.author == message.author) and (m.content in ['ぐー', 'ちょき', 'ぱー'])
    
    reply = await client.wait_for("message", check=jankencheck)

    if reply.content == jkbot:
      judge = draw
    else:
      if reply.content == "ぐー":
        if jkbot == "ちょき":
          judge = wn
        else:
          judge = lst

      elif reply.content == "ちょき":
        if jkbot == "ぱー":
          judge = wn
        else:
          judge = lst

      else:
        if jkbot == "ぐー":
          judge = wn
        else:
          judge = lst

    await message.channel.send(judge)

# Repl.it接続
keep_alive()

# Botの起動とDiscordサーバーへの接続
client.run(TOKEN)