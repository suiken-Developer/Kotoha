#インポート群
from __future__ import unicode_literals
import discord #基本
from discord.ext import commands
#from discord.ext import pages
import os
#import sys
from server import keep_alive
#import traceback
import random #さいころ
from googlesearch import search #画像検索
#import time #Ping
import datetime
import time
import shutil
#import threading
import asyncio #タイマー
import json #json利用
import requests #zip用
#from youtube_dl import YoutubeDL
#from lib import uranai #占い
#読み上げ
#import html
from discord.channel import VoiceChannel
#from gtts import gTTS
import re
from discord_slash import SlashCommand, SlashContext #Slash
from discord_slash.utils.manage_commands import create_option #Slash
from discord_together import DiscordTogether
from PIL import Image, ImageDraw, ImageFilter, ImageFont
#from discord_components import DiscordComponents, ComponentsBot, Button, ButtonStyle


#変数群
TOKEN = os.getenv("TOKEN") #トークン
ICON = os.getenv("ICON") #アイコンURL
prefix = 'k.' #Prefix
Bot_Version = '2.12.1'
Voice = 0

voiceChannel: VoiceChannel

players = {}

#embed_help = discord.Embed(title="Akane コマンドリスト",description="※現在は仮運用中です\nk.neko…にゃーん\nk.invite…このBotの招待リンクを表示するよ\nk.dice…サイコロを振るよ\nk.kuji…おみくじをひくよ\nk.search…Googleで検索をするよ（上位3件）\nk.janken…じゃんけんをするよ\nk.ping…BotのPingを取得するよ\n\n（このBotは開発中です。機能追加など要望も受付中です。）")
ModeFlag = 0 #Google検索モードオフ

#メンバーインテント
intents = discord.Intents.all()
intents.members = True

#接続に必要なオブジェクトを生成
#client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix=prefix, intents=intents, help_command=None)

#Slashのオブジェクト生成
slash_client = SlashCommand(bot, sync_commands=True)

#-----------------------
#DiscordComponents(bot)
#-----------------------

def add_text_to_image(img, text, font_path, font_size, font_color, height, width):
    position = (width, height)
    font = ImageFont.truetype(font_path, font_size)
    draw = ImageDraw.Draw(img)

    draw.text(position, text, font_color, font=font)

    return img


#起動時に動作する処理
@bot.event
async def on_ready():
    # 起動したらターミナルにログイン通知が表示される
    print('[Akane] ログインしました')
    bot.togetherControl = await DiscordTogether(TOKEN) 
    bot_guilds = len(bot.guilds)
    bot_members = []
    for guild in bot.guilds:
      for member in guild.members:
        if member.bot:
          pass
        else:
          bot_members.append(member)
    #activity = discord.Streaming(name='k.help でヘルプ | ' + str(bot_guilds) + ' Guilds ', url="https://www.twitch.tv/discord")
    activity = discord.Streaming(name='Akane 起動完了', url="https://www.twitch.tv/discord")
    await bot.change_presence(activity=activity)
    #起動メッセージをHereBots Hubに送信（チャンネルが存在しない場合、スルー）
    try:
      ready_log = bot.get_channel(800380094375264318)
      embed = discord.Embed(title="Akane 起動完了",description="**Akane#0940** が起動しました。\n```サーバー数: " + str(bot_guilds) + "\nユーザー数: " + str(len(bot_members)) + "```", timestamp=datetime.datetime.now())
      embed.set_footer(text="Akane - Ver" + Bot_Version,icon_url=ICON)
      await ready_log.send(embed=embed)
    except:
      pass

    activity_count = 0
    activity_list = ['❓Help: /help', str(bot_guilds) + ' Servers', str(len(bot_members) + 9000) + ' Users']
    while True:
      await asyncio.sleep(10)
      try:
        await bot.change_presence(activity=discord.Streaming(name=activity_list[activity_count], url="https://www.twitch.tv/discord"))
      except:
        pass
      if activity_count == len(activity_list) - 1:
        activity_count = 0
      else:
        activity_count = activity_count + 1


#スラッシュコマンド受信時に動作する処理

'''@bot.slash_command()
async def test_pages(ctx):
    await ctx.defer()
    test_pages = ['Page-One', 'Page-Two', 'Page-Three', 'Page-Four', 'Page-Five']
    paginator = pages.Paginator(pages=test_pages)
    await paginator.send(ctx)'''

#ヘルプ
@slash_client.slash(name="help", description="このBotのヘルプを表示します")
async def _slash_help(ctx: SlashContext):
    embed = discord.Embed(title="📖コマンドリスト",description="```Akane コマンドリストです。/ + <ここに記載されているコマンド> の形で送信することで、コマンドを実行することが出来ます。```\n**🤖Botコマンド**\n`help`, `invite`, `ping`\n\n**⭐機能系コマンド**\n`neko`, `dice`, `kuji`, `search`, `janken`, `userinfo`, `getguildicon`, `kick`, `ban`, `unban`\n\n**ゲーム系コマンド**\n`poker`, `chess`, `fishing`, `betrayal`, `youtube`\n（※このBotは開発中のため、機能追加等の提案も募集しています。）\n連絡は`HereBranch#5679`まで")
    embed.set_footer(text="❓コマンドの説明: k.help <コマンド名>")
    await ctx.send(embed=embed)

#neko
@slash_client.slash(name="neko", description="鳴きます")
async def _slash_neko(ctx: SlashContext):
    await ctx.send('にゃーん')

#招待リンク
@slash_client.slash(name="invite", description="このBotの招待リンクを表示します")
async def _slash_invite(ctx: SlashContext):
    embed = discord.Embed(title="招待リンク",description="こちらから、サーバー管理権限を持ったユーザーでAkaneの招待が出来ます。\nAkaneの権限: 管理者 ＜必須＞\nhttps://www.herebots.ml/akane",color=0xdda0dd)
    await ctx.send(embed=embed)

#じゃんけん
@slash_client.slash(name="janken", description="じゃんけん")
async def _slash_janken(ctx: SlashContext):
  await ctx.send("最初はぐー、じゃんけん（ぐー・ちょき・ぱーのどれかで送信してや）")
  
  jkbot = random.choice(("ぐー", "ちょき", "ぱー"))
  draw = "私は" + jkbot + "。" + "引き分け～"
  wn = "私は" + jkbot + "。" + "君の勝ち！"
  lst = random.choice(("私は" + jkbot + "。" + "私の勝ち！やったぁ","私は" + jkbot + "。" + "私の勝ちだね(∩´∀｀)∩、また挑戦してね！"))

  def jankencheck(m):
    return (m.author == ctx.author) and (m.content in ['ぐー', 'ちょき', 'ぱー'])
  
  reply = await bot.wait_for("message", check=jankencheck)

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

  await ctx.send(judge)

#dice
@slash_client.slash(name="dice", description="サイコロ（1～6）を振ります")
async def _slash_dice(ctx: SlashContext):
    word_list = [":one:",":two:",":three:",":four:",":five:",":six:"] 
    await ctx.send(random.choice(word_list) + 'が出たよ')

#ping
@slash_client.slash(name="ping", description="このBotのPingを確認します")
async def _slash_ping(ctx: SlashContext):
    embed = discord.Embed(title="📤Ping", description="`{0}ms`".format(round(bot.latency*1000, 2)), color=0xc8ff00)
    await ctx.send(embed=embed)

#kuji
@slash_client.slash(name="kuji", description="おみくじを引きます")
async def _slash_kuji(ctx: SlashContext):
    omikuji_list = ["大大凶", "大凶", "凶", "末吉", "小吉", "中吉", "吉", "大吉", "大大吉"]
    await ctx.send('今日の運勢は...** ' + random.choice(omikuji_list) + '**！')

#userinfo
@slash_client.slash(name="userinfo", description="ユーザー情報を取得します", options=[create_option(name="user",
 description="ユーザーをメンションまたはユーザーIDで指定", option_type=3, required=True)])
async def _slash_userinfo(ctx: SlashContext, user):
    #メンションからID抽出
    target = re.sub("\\D", "", str(user))
    #ユーザーIDからユーザーを取得

    try:
      user = await bot.fetch_user(target)
      #できなかったらエラー出す
    except:
      embed = discord.Embed(title=":x: エラー",description="そのユーザーを取得できませんでした",color=0xff0000)
      await ctx.send(embed=embed)

    else:
      embed = discord.Embed(title="ID",description=target,color=discord.Colour.green())
      try:
        embed.set_author(name=user, icon_url=user.avatar_url)
        embed.set_thumbnail(url=user.avatar_url)
      except:
        pass
      #embed.add_field(name="ニックネーム", value=user.nick,inline=True)
      #embed.add_field(name="ステータス", value=user.status,inline=True)
      #embed.add_field(name="ステータス", value=user.status,inline=False)
      embed.add_field(name="メンション", value=user.mention,inline=True)
      embed.set_footer(text="アカウント作成日時: {0}".format(user.created_at))
      await ctx.send(embed=embed)

#zip
'''
@slash_client.slash(name="zip", description=".zipファイルの中身を確認します", options=[create_option(name="url",
 description="ファイルのURLを指定", option_type=3, required=True)])
async def _slash_zip(ctx: SlashContext, url):
    try:
      link = str(url)
      response = requests.head(link, allow_redirects=True)
      size = response.headers.get('content-length', -1)
      #できなかったらエラー出す
    except:
      embed = discord.Embed(title=":x: エラー",description="ファイルを取得できませんでした",color=0xff0000)
      await ctx.send(embed=embed)

    else:
      if int(zip) > 8192:
        embed = discord.Embed(title=":x: エラー",description="8MBを超えるファイルは読み込めません",color=0xff0000)

      else:
        file_name = os.path.basename(url)
        embed = discord.Embed(title=":inbox_tray: ダウンロードして読み込み中...",description="ファイル名: {0}".format(file_name))
        msg = await ctx.send(embed=embed)
        
        urldata = requests.get(url).content

        unix = int(time.time())
        file_name_now = str(file_name) + "." + str(unix) + ".zip"
        
        with open(file_name_now ,mode='wb') as f:
          f.write(urldata)

        embed = discord.Embed(title=":file_folder: 解凍中...",description="ファイル名: {0}".format(file_name))
        await msg.edit(embed=embed)
        
        shutil.unpack_archive(file_name_now, file_name_now[:-4])

        
        def tree(path, layer=0, is_last=False, indent_current='　'):
          if not pathlib.Path(path).is_absolute():
              path = str(pathlib.Path(path).resolve())
      
          # カレントディレクトリの表示
          current = path.split('/')[::-1][0]
          if layer == 0:
              print('<'+current+'>')
          else:
              branch = '└' if is_last else '├'
              print('{indent}{branch}<{dirname}>'.format(indent=indent_current, branch=branch, dirname=current))
      
          # 下の階層のパスを取得
          paths = [p for p in glob.glob(path+'/*') if os.path.isdir(p) or os.path.isfile(p)]
          def is_last_path(i):
              return i == len(paths)-1
      
          # 再帰的に表示
          for i, p in enumerate(paths):
      
              indent_lower = indent_current
              if layer != 0:
                  indent_lower += '　　' if is_last else '│　'
      
              if os.path.isfile(p):
                  branch = '└' if is_last_path(i) else '├'
                  print('{indent}{branch}{filename}'.format(indent=indent_lower, branch=branch, filename=p.split('/')[::-1][0]))
              if os.path.isdir(p):
                  tree(p, layer=layer+1, is_last=is_last_path(i), indent_current=indent_lower)

        tree("/{0}".format(file_name_now[:-4]))
'''

#youtubedl
'''
@slash_client.slash(name="ytdl", description="YouTube動画のダウンロードリンクを取得します", options=[create_option(name="url",
 description="動画のURLを指定", option_type=3, required=True)])
async def _slash_zip(ctx: SlashContext, url):
    #try:
    youtube_dl_opts = {'writeautomaticsub': 'False',}
    
    with YoutubeDL(youtube_dl_opts) as ydl:
      info_dict = ydl.extract_info(url, download=False)
      video_title = info_dict['title'][0]
      mp3_url = info_dict['formats']['url']
      video_url = info_dict['url'][0]

    embed = discord.Embed(title="ダウンロードリンク",description="`{0}`のダウンロードリンクを取得しました。\n\n[クリックしてダウンロード]({1})\n:warning: 違法なコンテンツのダウンロードは法律で罰せられます".format(video_title, video_url),color=discord.Colour.red())
    await ctx.send(embed=embed)
      
      #できなかったらエラー出す
    except:
      embed = discord.Embed(title=":x: エラー",description="リンクを取得できませんでした。\nURLが正しいか確認してください。",color=0xff0000)
      await ctx.send(embed=embed)'''
      

#card
@slash_client.slash(name="card", description="ユーザーカードを作成します")
async def _slash_card(ctx: SlashContext):
  await ctx.author.avatar_url.save("icon.png")
  icon_path = "icon.png"
  base_image_path = 'card.png'
  base_img = Image.open(base_image_path).copy()
  icon = Image.open(icon_path).convert("RGBA")

  icon = icon.resize(size=(190, 190), resample=Image.ANTIALIAS)


  mask = Image.new("L", icon.size, 0)
  draw = ImageDraw.Draw(mask)
  draw.ellipse((0, 0, icon.size[0], icon.size[1]), fill=255)
  mask = mask.filter(ImageFilter.GaussianBlur(1))
  icon.putalpha(mask)

  song_title = "{0}#{1}".format(ctx.author.name, ctx.author.discriminator)
  font_path = "BIZ-UDGothicR.ttc"
  font_size = 57
  font_color = (255, 255, 255)
  height = 105
  width = 330
  #img = add_text_to_image(base_img, song_title, font_path, font_size, font_color, height, width)

  base_img.paste(icon, (40, 40), icon)
  base_img.save("test.png", format="png")
  await ctx.send(file=discord.File("test.png"))

#kick
@slash_client.slash(name="kick", description="メンバーのキックをします", options=[create_option(name="user",
 description="ユーザーをメンションまたはユーザーIDで指定", option_type=3, required=True)])
#[create_option(name="user",description="ユーザーをメンションまたはユーザーIDで指定", option_type=3, required=True),create_option(name="reason",description="Kick理由", option_type=3, required=False)]
async def _slash_kick(ctx: SlashContext, user):
    #メンションからID抽出
    target = re.sub("\\D", "", str(user))
    #ユーザーIDからユーザーを取得

    #実行者に管理者権限があるか
    if not ctx.author.guild_permissions.administrator == True:
        embed = discord.Embed(
            title=":x: エラー",
            description="あなたには管理者権限がないため、このコマンドを実行する権限がありません。",
            color=0xff0000)
        await ctx.send(embed=embed)

    else:
    
      try:
        user = await bot.fetch_user(target)
        #できなかったらエラー出す
      except:
        embed = discord.Embed(title=":x: エラー",description="そのユーザーを取得できませんでした",color=0xff0000)
        await ctx.send(embed=embed)

      else:
        try:
          #await ctx.guild.kick(user, reason=reason)
          await ctx.guild.kick(user)
        except:
          embed = discord.Embed(title=":x: エラー",description="そのユーザーをKickできません",color=0xff0000)
          await ctx.send(embed=embed)
        else:
          embed = discord.Embed(title=":white_check_mark: 成功",description="Kickが完了しました。\n",timestamp=datetime.datetime.now(),color=discord.Colour.green())
          try:
            embed.set_thumbnail(url=user.avatar_url)
          except:
            pass
          #if not reason:
          #    reason = "理由がありません"
          embed.add_field(name="**Kickされたユーザー**",value="{0} [ID:{1}]".format(str(user), target),inline=False)
          #embed.add_field(name="**理由**",value="{0}".format(str(reason),inline=False))
          embed.add_field(name="**実行者**",value="{0}".format(str("<@!" + str(ctx.author.id) + ">"),inline=False))
          await ctx.send(embed=embed)

#ban
@slash_client.slash(name="ban", description="メンバーのBANをします", options=[create_option(name="user",
 description="ユーザーをメンションまたはユーザーIDで指定", option_type=3, required=True)])
async def _slash_ban(ctx: SlashContext, user):
    #メンションからID抽出
    target = re.sub("\\D", "", str(user))
    #ユーザーIDからユーザーを取得

    #実行者に管理者権限があるか
    if not ctx.author.guild_permissions.administrator == True:
        embed = discord.Embed(
            title=":x: エラー",
            description="あなたには管理者権限がないため、このコマンドを実行する権限がありません。",
            color=0xff0000)
        await ctx.send(embed=embed)

    else:
    
      try:
        user = await bot.fetch_user(target)
        #できなかったらエラー出す
      except:
        embed = discord.Embed(title=":x: エラー",description="そのユーザーを取得できませんでした",color=0xff0000)
        await ctx.send(embed=embed)

      else:
        try:
          await ctx.guild.ban(user, reason="{0}さんによってBANが実行されました".format(ctx.author.id), delete_message_days=0)
        except:
          embed = discord.Embed(title=":x: エラー",description="そのユーザーをBANできません",color=0xff0000)
          await ctx.send(embed=embed)
        else:
          embed = discord.Embed(title=":white_check_mark: 成功",description="BANが完了しました。\n",timestamp=datetime.datetime.now(),color=discord.Colour.green())
          try:
            embed.set_thumbnail(url=user.avatar_url)
          except:
            pass
          #if not reason:
          #    reason = "理由がありません"
          embed.add_field(name="**BANされたユーザー**",value="{0} [ID:{1}]".format(str("<@!" + str(target) + ">"), target),inline=False)
          #embed.add_field(name="**理由**",value="{0}".format(str(reason),inline=False))
          embed.add_field(name="**実行者**",value="{0}".format(str("<@!" + str(ctx.author.id) + ">"),inline=False))
          await ctx.send(embed=embed)

#unban
@slash_client.slash(name="unban", description="メンバーのBAN解除をします", options=[create_option(name="user",
 description="ユーザーをメンションまたはユーザーIDで指定", option_type=3, required=True)])
async def _slash_unban(ctx: SlashContext, user):
    #メンションからID抽出
    target = re.sub("\\D", "", str(user))
    #ユーザーIDからユーザーを取得

    #実行者に管理者権限があるか
    if not ctx.author.guild_permissions.administrator == True:
        embed = discord.Embed(
            title=":x: エラー",
            description="あなたには管理者権限がないため、このコマンドを実行する権限がありません。",
            color=0xff0000)
        await ctx.send(embed=embed)

    else:
    
      try:
        user = await bot.fetch_user(target)
        #できなかったらエラー出す
      except:
        embed = discord.Embed(title=":x: エラー",description="そのユーザーを取得できませんでした",color=0xff0000)
        await ctx.send(embed=embed)

      else:
        try:
          await ctx.guild.unban(user)
        except:
          embed = discord.Embed(title=":x: エラー",description="そのユーザーをBAN解除できません",color=0xff0000)
          await ctx.send(embed=embed)
        else:
          embed = discord.Embed(title=":white_check_mark: 成功",description="BAN解除が完了しました。\n",timestamp=datetime.datetime.now(),color=discord.Colour.green())
          try:
            embed.set_thumbnail(url=user.avatar_url)
          except:
            pass
          #if not reason:
          #    reason = "理由がありません"
          embed.add_field(name="**BAN解除されたユーザー**",value="{0} [ID:{1}]".format(str(user), target),inline=False)
          #embed.add_field(name="**理由**",value="{0}".format(str(reason),inline=False))
          embed.add_field(name="**実行者**",value="{0}".format(str("<@!" + str(ctx.author.id) + ">"),inline=False))
          await ctx.send(embed=embed)


#delete
@slash_client.slash(name="delete", description="メッセージを削除します", options=[create_option(name="num",
 description="削除件数を指定", option_type=3, required=True)])
async def _slash_delete(ctx: SlashContext,num):

    #実行者に管理者権限があるか
    if not ctx.author.guild_permissions.administrator == True:
        embed = discord.Embed(
            title=":x: エラー",
            description="あなたには管理者権限がないため、このコマンドを実行する権限がありません。",
            color=0xff0000)
        await ctx.send(embed=embed)

    else:
      channel = ctx.channel
      try:
        deleted = await channel.purge(limit=int(num))

      except:
        embed = discord.Embed(
          title=":x: エラー",
          description="エラーが発生しました",
          color=0xff0000)
        await ctx.send(embed=embed)

      else:
        embed = discord.Embed(
          title=":white_check_mark: 成功",
          description="`{0}`メッセージを削除しました".format(len(deleted)),
          color=discord.Colour.green())
        await ctx.send(embed=embed)

#Google検索
@slash_client.slash(name="search", description="Google検索をします", options=[create_option(name="word",
 description="検索語句を指定", option_type=3, required=True)])
async def _slash_search(ctx: SlashContext, word):
    search_send = await ctx.send('**検索中...**')
    start = time.time()
    searched = []
    #g_url = 'https://www.google.co.jp/search'
    count = 0
    for url in search(word, lang="jp",num = 3):
      searched.append(url)
      count += 1
      if(count == 3):
        stop = time.time()
        embed = discord.Embed(title="検索結果",description=":one: " + searched[0] + "\n:two: " + searched[1] + "\n:three: " + searched[2])
        await search_send.edit(content="検索しました（{0}秒）".format(stop-start), embed=embed)
        break

#GuildIcon
@slash_client.slash(name="getguildicon", description="このサーバーのアイコンを取得します")
async def _slash_getguildicon(ctx: SlashContext):
  try:
    guildicon = ctx.guild.icon_url_as(static_format='png')
  except:
    embed = discord.Embed(title=":x: エラー",
                              description="サーバーアイコンを取得できません",
                              color=0xff0000)
    await ctx.send(embed=embed)
  else:
    embed = discord.Embed(
    title="サーバーアイコン",
    description=":white_check_mark:画像を取得しました。")
    embed.set_thumbnail(url=guildicon)
    await ctx.send(embed=embed)

#YouTube Together
@slash_client.slash(name="youtube", description="ボイスチャンネルでYouTubeの再生を開始します")
async def _slash_youtube(ctx: SlashContext):
  try:
    link = await bot.togetherControl.create_link(ctx.author.voice.channel.id, 'youtube')
  except:
    embed = discord.Embed(title=":x: エラー",description="ボイスチャンネルに参加してください",color=0xff0000)
    await ctx.send(embed=embed)
  else:
    embed = discord.Embed(title="YouTube",description="[クリック]({0})して開始！\n※二人目以降の方は押す必要はありません".format(link),color=discord.Colour.red())
    await ctx.send(embed=embed)

#Poker
@slash_client.slash(name="poker", description="ボイスチャンネルでPoker Nightを開始します")
async def _slash_poker(ctx: SlashContext):
  try:
    link = await bot.togetherControl.create_link(ctx.author.voice.channel.id, 'poker')
  except:
    embed = discord.Embed(title=":x: エラー",description="ボイスチャンネルに参加してください",color=0xff0000)
    await ctx.send(embed=embed)
  else:
    embed = discord.Embed(title="Poker Night",description="[クリック]({0})して開始！\n認証画面が表示されたら、認証ボタンをクリックして下さい。\n※二人目以降の方は押す必要はありません\n※18歳以上のみご利用できます".format(link),color=discord.Colour.dark_blue())
    await ctx.send(embed=embed)

#Chess
@slash_client.slash(name="chess", description="ボイスチャンネルでChess in the Parkを開始します")
async def _slash_chess(ctx: SlashContext):
  try:
    link = await bot.togetherControl.create_link(ctx.author.voice.channel.id, 'chess')
  except:
    embed = discord.Embed(title=":x: エラー",description="ボイスチャンネルに参加してください",color=0xff0000)
    await ctx.send(embed=embed)
  else:
    embed = discord.Embed(title="Chess in the Park",description="[クリック]({0})して開始！\n認証画面が表示されたら、認証ボタンをクリックして下さい。\n※二人目以降の方は押す必要はありません".format(link),color=discord.Colour.dark_green())
    await ctx.send(embed=embed)

#Betrayal.io
@slash_client.slash(name="betrayal", description="ボイスチャンネルでBetrayal.ioを開始します")
async def _slash_betrayal(ctx: SlashContext):
  try:
    link = await bot.togetherControl.create_link(ctx.author.voice.channel.id, 'betrayal')
  except:
    embed = discord.Embed(title=":x: エラー",description="ボイスチャンネルに参加してください",color=0xff0000)
    await ctx.send(embed=embed)
  else:
    embed = discord.Embed(title="Betrayal.io",description="[クリック]({0})して開始！\n認証画面が表示されたら、認証ボタンをクリックして下さい。\n※二人目以降の方は押す必要はありません".format(link),color=discord.Colour.dark_gold())
    await ctx.send(embed=embed)

#Fishington.io
@slash_client.slash(name="fishing", description="ボイスチャンネルでFishington.ioを開始します")
async def _slash_fishing(ctx: SlashContext):
  try:
    link = await bot.togetherControl.create_link(ctx.author.voice.channel.id, 'fishing')
  except:
    embed = discord.Embed(title=":x: エラー",description="ボイスチャンネルに参加してください",color=0xff0000)
    await ctx.send(embed=embed)
  else:
    embed = discord.Embed(title="Fishington.io",description="[クリック]({0})して開始！\n認証画面が表示されたら、認証ボタンをクリックして下さい。\n※二人目以降の方は押す必要はありません".format(link),color=discord.Colour.dark_blue())
    await ctx.send(embed=embed)

#Letter Tile
@slash_client.slash(name="letter-tile", description="ボイスチャンネルでLetter Tileを開始します")
async def _slash_lettertile(ctx: SlashContext):
  try:
    link = await bot.togetherControl.create_link(ctx.author.voice.channel.id, 'letter-tile')
  except:
    embed = discord.Embed(title=":x: エラー",description="ボイスチャンネルに参加してください",color=0xff0000)
    await ctx.send(embed=embed)
  else:
    embed = discord.Embed(title="Letter Tile",description="[クリック]({0})して開始！\n認証画面が表示されたら、認証ボタンをクリックして下さい。\n※二人目以降の方は押す必要はありません".format(link),color=0x00ff7f)
    await ctx.send(embed=embed)

#Word Snack
@slash_client.slash(name="word-snack", description="ボイスチャンネルでWord Snackを開始します")
async def _slash_wordsnack(ctx: SlashContext):
  try:
    link = await bot.togetherControl.create_link(ctx.author.voice.channel.id, 'word-snack')
  except:
    embed = discord.Embed(title=":x: エラー",description="ボイスチャンネルに参加してください",color=0xff0000)
    await ctx.send(embed=embed)
  else:
    embed = discord.Embed(title="Word Snack",description="[クリック]({0})して開始！\n認証画面が表示されたら、認証ボタンをクリックして下さい。\n※二人目以降の方は押す必要はありません".format(link),color=0xdaa520)
    await ctx.send(embed=embed)

#Doodle Crew
@slash_client.slash(name="doodle-crew", description="ボイスチャンネルでDoodle Crewを開始します")
async def _slash_doodlecrew(ctx: SlashContext):
  try:
    link = await bot.togetherControl.create_link(ctx.author.voice.channel.id, 'doodle-crew')
  except:
    embed = discord.Embed(title=":x: エラー",description="ボイスチャンネルに参加してください",color=0xff0000)
    await ctx.send(embed=embed)
  else:
    embed = discord.Embed(title="Doodle Crew",description="[クリック]({0})して開始！\n認証画面が表示されたら、認証ボタンをクリックして下さい。\n※二人目以降の方は押す必要はありません".format(link),color=0xffa500)
    await ctx.send(embed=embed)

#SpellCast
@slash_client.slash(name="spellcast", description="ボイスチャンネルでSpellCastを開始します")
async def _slash_spellcast(ctx: SlashContext):
  try:
    link = await bot.togetherControl.create_link(ctx.author.voice.channel.id, 'spellcast')
  except:
    embed = discord.Embed(title=":x: エラー",description="ボイスチャンネルに参加してください",color=0xff0000)
    await ctx.send(embed=embed)
  else:
    embed = discord.Embed(title="SpellCast",description="[クリック]({0})して開始！\n認証画面が表示されたら、認証ボタンをクリックして下さい。\n※二人目以降の方は押す必要はありません".format(link),color=0x1e90ff)
    await ctx.send(embed=embed)

#Awkword
@slash_client.slash(name="awkword", description="ボイスチャンネルでAwkwordを開始します")
async def _slash_awkword(ctx: SlashContext):
  try:
    link = await bot.togetherControl.create_link(ctx.author.voice.channel.id, 'awkword')
  except:
    embed = discord.Embed(title=":x: エラー",description="ボイスチャンネルに参加してください",color=0xff0000)
    await ctx.send(embed=embed)
  else:
    embed = discord.Embed(title="Awkword",description="[クリック]({0})して開始！\n認証画面が表示されたら、認証ボタンをクリックして下さい。\n※二人目以降の方は押す必要はありません".format(link),color=0x000000)
    await ctx.send(embed=embed)

#Checkers in the Park	
@slash_client.slash(name="checkers", description="ボイスチャンネルでCheckers in the Park	を開始します")
async def _slash_checkers(ctx: SlashContext):
  try:
    link = await bot.togetherControl.create_link(ctx.author.voice.channel.id, 'checkers')
  except:
    embed = discord.Embed(title=":x: エラー",description="ボイスチャンネルに参加してください",color=0xff0000)
    await ctx.send(embed=embed)
  else:
    embed = discord.Embed(title="Checkers in the Park	",description="[クリック]({0})して開始！\n認証画面が表示されたら、認証ボタンをクリックして下さい。\n※二人目以降の方は押す必要はありません".format(link),color=0x2f4f4f)
    await ctx.send(embed=embed)


#workn
@slash_client.slash(name="workn", description="ワークん" ,guild_ids=[831519184240115712, 883709673889497138])
async def _slash_workn(ctx: SlashContext):
  workns = ["呼ばれてるでー", "おーい", "元気？", "調子はどや？", "おはようさん", "せやなぁ！", "ワークん！！"]
  n = random.choice([0, 1, 2, 3, 4, 5, 6])

  workn = workns[n]
  
  await ctx.send('{0}<@818092163090874369>'.format(workn))

'''
@slash_client.slash(name="translate", description="翻訳します", options=[create_option(name="language",
 description="翻訳先言語を指定", option_type=3, required=True), create_option(name="text",
 description="翻訳する文章を指定（400）文字まで", option_type=3, required=True)])
async def _slash_translate(ctx: SlashContext, language, text):
  if len(text) > 400:
    embed = discord.Embed(title=":x: エラー",description="文字数が超過しています",color=0xff0000)
    await ctx.send(embed=embed)

  translator = Translator()
  translated = translator.translate(text, dest=language)
  try:
    translated = translator.translate(text, dest=language)
  except:
    embed = discord.Embed(title=":x: エラー", description="翻訳先言語が間違っているもしくはレート制限（24時間使用できません）されています。",color=0xff0000)
    await ctx.send(embed=embed)
  else:
    embed = discord.Embed(title="翻訳",description=translated.text,color=discord.Colour.dark_blue())
    await ctx.send(embed=embed)
'''

'''
#YouTube
@slash_client.slash(name="join", description="音声チャンネルに参加します")
async def _slash_join(ctx: SlashContext):
    channel = ctx.author.voice.channel
    voice = get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        voice = await channel.connect()

#URLから再生
@slash_client.slash(name="play", description="音楽を再生します", options=[create_option(name="url",
 description="URLを指定", option_type=3, required=True)])
async def _slash_play(ctx: SlashContext, url):
    YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    voice = get(bot.voice_clients, guild=ctx.guild)

    if not voice.is_playing():
        with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
        URL = info['url']
        voice.play(FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))
        voice.is_playing()
        await ctx.send(':white_check_mark: **再生を開始しました**')

# check if the bot is already playing
    else:
        await ctx.send(":x: すでに再生しています")
        return

#再開
@slash_client.slash(name="resume", description="音楽の再生を再開します")
async def _slash_resume(ctx: SlashContext):
    voice = get(bot.voice_clients, guild=ctx.guild)

    if not voice.is_playing():
        voice.resume()
        await ctx.send('再生を再開しました')

@slash_client.slash(name="pause", description="音楽の再生を一時停止します")
async def _slash_pause(ctx: SlashContext):
    voice = get(bot.voice_clients, guild=ctx.guild)

    if voice.is_playing():
        voice.pause()
        await ctx.send('再生を一時停止しました')

@slash_client.slash(name="stop", description="音楽の再生を停止します")
async def _slash_stop(ctx: SlashContext):
    voice = get(bot.voice_clients, guild=ctx.guild)

    if voice.is_playing():
        voice.stop()
        await ctx.send('停止しています...')

'''

#janken
'''
@slash_client.slash(name="btn", description="btn", guild_ids=[589312721506271236])
async def _slash_btn(ctx: SlashContext):

  buttons = [
    create_button(style=ButtonStyle.green, label="ぐー"),
    create_button(style=ButtonStyle.blue, label="ちょき"),
    create_button(style=ButtonStyle.red, label="ぱー")
  ]
  action_row = create_actionrow(*buttons)

  await ctx.send("最初はぐー、じゃんけん（ぐー・ちょき・ぱーのどれかを押してね）", components=[action_row])'''



#メッセージ受信時に動作する処理

@bot.command()
async def help(ctx, *arg):
  if ctx.author.bot:
    return

  if arg:
    with open('data/commands.json', encoding='utf-8') as f:
      commands = json.load(f)
      print(arg[0])

    if str(arg[0]) in commands:
      category = commands[str(arg[0])]["category"]
      help_usage = commands[str(arg[0])]["usage"]
      help_info = commands[str(arg[0])]["info"]
      embed = discord.Embed(title=category + ": **" + str(arg[0]) + "**",description="")
      embed.add_field(name="使い方", value="\n```" + prefix + help_usage + "```",inline=False)
      embed.add_field(name="説明", value="```" + help_info + "```",inline=False)
      embed.set_footer(text="<> : 必要引数 | [] : オプション引数")
      await ctx.send(embed=embed)

  #なければ通常
  else:
    embed = discord.Embed(title="📖コマンドリスト",description="Prefix: `" + prefix + "`\n```Akane コマンドリストです。Prefix + <ここに記載されているコマンド> の形で送信することで、コマンドを実行することが出来ます。```\n**全てのコマンドはスラッシュコマンドに移行しました。**`/ + <コマンド>`の形で実行できます。\nコマンドの説明のみ`k.help <コマンド名>`で閲覧可能です。")
    await ctx.send(embed=embed)


@bot.event
async def on_message(ctx):
  if ctx.author.bot:
    return

  if ctx.content == "せやな":
    #i = random.choice([0, 1])

    await ctx.channel.send("<:Seyana:851104856110399488>")

  if ctx.channel.name == "akane-talk":
    reps = ["あ ほ く さ", "あほくさ", "せやな", "あれな", "ええで", "ええんちゃう？", "ほんま", "知らんがな", "知らんけど～", "それな", "そやな", "わかる", "なんや", "うん", "どしたん？", "やめたら？そのゲーム", "な。", "うん？", "わかる（感銘）", "わかる（天下無双）", "マ？", "Sorena...", "はよ", "Seyana...", "や↑ったぜ", "なに買って来たん？", "ほかには？", "そぉい！", "ウマいやろ？", ""]
    i = random.choice(reps)
    await ctx.channel.send(i)

'''
@client.event
async def on_message(message):
  global ModeFlag, result, judge, voiceChannel, Voice
  if message.author.bot:
    return

  #ヘルプメニュー
  if message.content.split(' ')[0] == prefix + "help":
    help_tmp = str(message.content)
    help_tmp = help_tmp.split(' ')
    with open('data/commands.json', encoding='utf-8') as f:
      commands = json.load(f)

    if str(help_tmp[1]) in commands:
        category = commands[str(help_tmp[1])]["category"]
        help_usage = commands[str(help_tmp[1])]["usage"]
        help_info = commands[str(help_tmp[1])]["info"]
        embed = discord.Embed(title=category + ": **" + str(help_tmp[1]) + "**",description="")
        embed.add_field(name="使い方", value="\n```" + prefix + help_usage + "```",inline=False)
        embed.add_field(name="説明", value="```" + help_info + "```",inline=False)
        embed.set_footer(text="<> : 必要引数 | [] : オプション引数")
        await message.channel.send(embed=embed)

    #引数があるか
    if len(help_tmp) == 2:
      if str(help_tmp[1]) in commands:
        category = commands[str(help_tmp[1])]["category"]
        help_usage = commands[str(help_tmp[1])]["usage"]
        help_info = commands[str(help_tmp[1])]["info"]
        embed = discord.Embed(title=category + ": **" + str(help_tmp[1]) + "**",description="")
        embed.add_field(name="使い方", value="\n```" + prefix + help_usage + "```",inline=False)
        embed.add_field(name="説明", value="```" + help_info + "```",inline=False)
        embed.set_footer(text="<> : 必要引数 | [] : オプション引数")
        await message.channel.send(embed=embed)
    
    #なければ通常
    else:
      embed = discord.Embed(title="📖コマンドリスト",description="Prefix: `" + prefix + "`\n```Akane コマンドリストです。Prefix + <ここに記載されているコマンド> の形で送信することで、コマンドを実行することが出来ます。```\n**全てのコマンドはスラッシュコマンドに移行しました。**`/ + <コマンド>`の形で実行できます。\nコマンドの説明のみ`k.help <コマンド名>`で閲覧可能です。")
      await message.channel.send(embed=embed)



  #にゃーん
  if message.content == prefix + 'neko':
    await message.channel.send('にゃーん')
  '''
'''
  if message.content == 'せやな':
    i = random.choice([0, 1])

    if i == 1:
      await message.channel.send("せやな")

    if i == 0:
      await message.channel.send("<:Seyana:851104856110399488>")

  if message.channel.name == "akane-talk":
      reps = ["あ ほ く さ", "せやな", "あれな", "ええで", "ええんちゃう？", "ほんま", "知らんがな", "知らんけど～", "それな", "そやな", "わかる", "なんや", "うん", "どしたん？", "やめたら？そのゲーム", "な。", "うん？", "わかる（感銘）", "わかる（天下無双）", "マ？", "Sorena...", "はよ"]
      i = random.choice(reps)
      await message.channel.send(i)

  #残高確認
  if message.content == prefix + "mcheck":
    with open('data/money.json', encoding='utf-8') as f:
      money = json.load(f)

    if not str(message.author.id) in money.keys():
      money[str(message.author.id)] = '{"money" : "", "enforcer" : "", "datetime" : ""}'

'''
 
'''   
  #招待リンク
  if message.content == prefix + 'invite':
      embed = discord.Embed(title="招待リンク",description="こちらのリンクから、サーバー管理権限を持ったユーザーでAkaneの招待が出来ます。（Akaneの権限: 管理者 ＜必須＞）\n\n**https://www.herebots.ml/akane**",color=0xdda0dd)
      await message.channel.send(embed=embed)
        
  #Ping
  if message.content == prefix + 'ping':
    embed = discord.Embed(title="📤Ping", description="`{0}ms`".format(round(client.latency*1000, 2)), color=0xc8ff00)
    await message.channel.send(embed=embed)

  #Dice
  if message.content == prefix + 'dice':
    word_list = [":one:",":two:",":three:",":four:",":five:",":six:"]
    await message.channel.send(random.choice(word_list) + 'が出たよ')

  #Kick
  if message.content.split(' ')[0] == prefix + "kick":
    tmp = str(message.content) #変数tmpにこのコマンド内容をすべて格納
    tmp = tmp.split(' ') #tmpを空白区切りにする

    #引数があるか（＝Kickするユーザーを指定しているか）
    if len(tmp) == 2:
      #メンションからID抽出
      tmp[1] = re.sub("\\D", "", str(tmp[1]))
      #ユーザーIDからユーザーを取得

      #実行者に管理者権限があるか
      if not message.author.guild_permissions.administrator == True:
          embed = discord.Embed(
              title=":x: エラー",
              description="あなたには管理者権限がないため、このコマンドを実行する権限がありません。",
              color=0xff0000)
          await message.channel.send(embed=embed)

      else:
      
        try:
          user = await client.fetch_user(tmp[1])
          #できなかったらエラー出す
        except:
          embed = discord.Embed(title=":x: エラー",description="そのユーザーを取得できませんでした",color=0xff0000)
          await message.channel.send(embed=embed)

        else:
          try:
            await message.guild.kick(user)
          except:
            embed = discord.Embed(title=":x: エラー",description="そのユーザーをKickできません",color=0xff0000)
            await message.channel.send(embed=embed)
          else:
            embed = discord.Embed(title=":white_check_mark: 成功",description="Kickが完了しました。\n",timestamp=datetime.datetime.now(),color=discord.Colour.green())
            try:
              embed.set_thumbnail(url=user.avatar_url)
            except:
              pass
            embed.add_field(name="**Kickされたユーザー**",value="{0} [ID:{1}]".format(str(user), tmp[1]),inline=False)
            embed.add_field(name="**実行者**",value="{0}".format(str("<@!" + str(message.author.id) + ">"),inline=False))
            await message.channel.send(embed=embed)
    
    #占い
  if message.content == prefix + 'kuji':
    omikuji_list = ["大大凶", "大凶", "凶", "末吉", "小吉", "中吉", "吉", "大吉", "大大吉"]
    await message.channel.send('今日の運勢は...** ' + random.choice(omikuji_list) + '**だよ！')

  #Google検索
  if message.content.split(' ')[0] == prefix + "search":
    gbaninfo_tmp = str(message.content)
    gbaninfo_tmp = gbaninfo_tmp.split(' ')

    #引数が正しく設定されているか
    try:
      gbaninfo_tmp = gbaninfo_tmp[1]
    except:
      embed = discord.Embed(title=":x: エラー",description="コマンドが不正です。引数が正しく設定されているか確認して下さい。",color=0xff0000)
      await message.channel.send(embed=embed)
    
    #引数として与えられたユーザーは存在するのか（Deleted User判別）
    else:
      search_send = await message.channel.send('**検索中...**')
      searched = []
      #g_url = 'https://www.google.co.jp/search'
      count = 0
      for url in search(gbaninfo_tmp, lang="jp",num = 3):
              searched.append(url)
              count += 1
              if(count == 3):
                  try:
                    await search_send.delete()
                  except:
                    pass

                  else:
                    embed = discord.Embed(title="検索結果",description=":one: " + searched[0] + "\n:two: " + searched[1] + "\n:three: " + searched[2])
                    await message.channel.send(embed=embed)
                    break
        
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
'''

keep_alive()

#Botの起動とDiscordサーバーへの接続
#429エラー防止
try:
  bot.run(TOKEN)

except:
  os.system("kill 1")