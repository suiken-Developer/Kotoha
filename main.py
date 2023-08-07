#インポート群
from __future__ import unicode_literals
import discord  #基本
import discord.app_commands
from discord.ext import commands
import os
from server import keep_alive
import random  #さいころ
from googlesearch.googlesearch import GoogleSearch  #画像検索
import datetime
import time
import shutil
import asyncio  #タイマー
import json  #json利用
import requests  #zip用
from yt_dlp import YoutubeDL
from discord.channel import VoiceChannel
import re
from discord_together import DiscordTogether
from PIL import Image, ImageDraw, ImageFilter, ImageFont

#変数群
TOKEN = os.getenv("TOKEN")  #トークン
ICON = os.getenv("ICON")  #アイコンURL
prefix = 'k.'  #Prefix
Bot_Version = '4.0.0β'
Voice = 0

voiceChannel: VoiceChannel

players = {}

ModeFlag = 0  #Google検索モードオフ

#メンバーインテント
intents = discord.Intents.all()
intents.members = True

#接続に必要なオブジェクトを生成
#client = discord.Client(intents=intents)
#bot = commands.Bot(command_prefix=prefix, intents=intents, help_command=None)

#Slashのオブジェクト生成
#slash_client = SlashCommand(bot, sync_commands=True)
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)


#-----------------------
#DiscordComponents(bot)
#-----------------------


def add_text_to_image(img, text, font_path, font_size, font_color, height,
                      width):
  position = (width, height)
  font = ImageFont.truetype(font_path, font_size)
  draw = ImageDraw.Draw(img)

  draw.text(position, text, font_color, font=font)

  return img


#起動時に動作する処理
@client.event
async def on_ready():
  # 起動したらターミナルにログイン通知が表示される
  print('[Akane] ログインしました')
  client.togetherControl = await DiscordTogether(TOKEN)
  bot_guilds = len(client.guilds)
  bot_members = []
  for guild in client.guilds:
    for member in guild.members:
      if member.bot:
        pass
      else:
        bot_members.append(member)
  #activity = discord.Streaming(name='k.help でヘルプ | ' + str(bot_guilds) + ' Guilds ', url="https://www.twitch.tv/discord")
  activity = discord.Streaming(name='Akane 起動完了',
                               url="https://www.twitch.tv/discord")
  await client.change_presence(activity=activity)
  #コマンドをSync
  try:
    await tree.sync()
  except:
    print("Failed to sync.")
  else:
    print("Commands synced.")
  #起動メッセージをHereBots Hubに送信（チャンネルが存在しない場合、スルー）
  try:
    ready_log = client.get_channel(800380094375264318)
    embed = discord.Embed(title="Akane 起動完了",
                          description="**Akane#0940** が起動しました。\n```サーバー数: " +
                          str(bot_guilds) + "\nユーザー数: " +
                          str(len(bot_members)) + "```",
                          timestamp=datetime.datetime.now())
    embed.set_footer(text="Akane - Ver" + Bot_Version, icon_url=ICON)
    await ready_log.send_message(embed=embed)
  except:
    pass

  activity_count = 0
  activity_list = [
    '❓Help: /help',
    str(bot_guilds) + ' Servers',
    str(len(bot_members) + 9000) + ' Users'
  ]
  while True:
    await asyncio.sleep(10)
    try:
      await client.change_presence(
        activity=discord.Streaming(name=activity_list[activity_count],
                                   url="https://www.twitch.tv/discord"))
    except:
      pass
    if activity_count == len(activity_list) - 1:
      activity_count = 0
    else:
      activity_count = activity_count + 1


#ヘルプ
@tree.command(name="help", description="このBotのヘルプを表示します")
@discord.app_commands.describe(command="指定したコマンドの説明を表示します")
async def help(ctx: discord.Interaction, command: str = None):
  if command:
    with open('data/commands.json', encoding='utf-8') as f:
      commands = json.load(f)
      print(command[0])

    if str(command[0]) in commands:
      category = commands[str(command[0])]["category"]
      help_usage = commands[str(command[0])]["usage"]
      help_info = commands[str(command[0])]["info"]
      embed = discord.Embed(title=category + ": **" + str(command[0]) + "**",
                            description="")
      embed.add_field(name="使い方",
                      value="\n```" + prefix + help_usage + "```",
                      inline=False)
      embed.add_field(name="説明", value="```" + help_info + "```", inline=False)
      embed.set_footer(text="<> : 必要引数 | [] : オプション引数")
      await ctx.response.send_message(embed=embed)

    else:
      embed = discord.Embed(
      title="📖コマンドリスト",
      description=
      "```Akane コマンドリストです。/ + <ここに記載されているコマンド> の形で送信することで、コマンドを実行することが出来ます。```\n**🤖Botコマンド**\n`help`, `invite`, `ping`\n\n**⭐機能系コマンド**\n`neko`, `dice`, `kuji`, `search`, `janken`, `userinfo`, `getguildicon`, `unban`,`ytdl`\n\n**ゲーム系コマンド**\n`poker`, `chess`, `youtube`\n（※このBotは開発中のため、機能追加等の提案も募集しています。）\n連絡は`@bz6 (Branch#7777)まで"
      )
      embed.set_footer(text="❓コマンドの説明: /help <コマンド名>")
      await ctx.response.send_message(embed=embed)

  else:
    embed = discord.Embed(
      title="📖コマンドリスト",
      description=
      "```Akane コマンドリストです。/ + <ここに記載されているコマンド> の形で送信することで、コマンドを実行することが出来ます。```\n**🤖Botコマンド**\n`help`, `invite`, `ping`\n\n**⭐機能系コマンド**\n`neko`, `dice`, `kuji`, `search`, `janken`, `userinfo`, `getguildicon`, `unban`\n\n**ゲーム系コマンド**\n`poker`, `chess`, `youtube`\n（※このBotは開発中のため、機能追加等の提案も募集しています。）\n連絡は`@bz6 (Branch#7777)まで"
      )
    embed.set_footer(text="❓コマンドの説明: /help <コマンド名>")
    await ctx.response.send_message(embed=embed)
  

#neko
@tree.command(name="neko", description="鳴きます")
async def neko(ctx: discord.Interaction):
  await ctx.response.send_message('にゃーん')


#招待リンク
@tree.command(name="invite", description="このBotの招待リンクを表示します")
async def invite(ctx: discord.Interaction):
  button = discord.ui.Button(label="招待する",style=discord.ButtonStyle.link,url="https://www.herebots.ml/akane")
  embed = discord.Embed(
    title="招待リンク",
    description=
    "以下のボタンから、サーバー管理権限を持ったユーザーでAkaneの招待が出来ます。",
    color=0xdda0dd)
  view = discord.ui.View()
  view.add_item(button)
  await ctx.response.send_message(embed=embed,view=view)

@tree.command(name="janken",description="じゃんけん")
async def janken(ctx: discord.Interaction):
    button1 = discord.ui.Button(label="ぐー",style=discord.ButtonStyle.primary,custom_id="j_g")
    button2 = discord.ui.Button(label="ちょき",style=discord.ButtonStyle.success,custom_id="j_c")
    button3 = discord.ui.Button(label="ぱー",style=discord.ButtonStyle.danger,custom_id="j_p")
    view = discord.ui.View()
    view.add_item(button1)
    view.add_item(button2)
    view.add_item(button3)
    await ctx.response.send_message("最初はぐー、じゃんけん",view=view)

#dice
@tree.command(name="dice", description="サイコロ（1～6）を振ります")
async def dice(ctx: discord.Interaction):
  word_list = [":one:", ":two:", ":three:", ":four:", ":five:", ":six:"]
  await ctx.response.send_message(random.choice(word_list) + 'が出たで')


#ping
@tree.command(name="ping", description="このBotのPingを確認します")
async def ping(ctx: discord.Interaction):
  embed = discord.Embed(title="📤Ping",
                        description="`{0}ms`".format(
                          round(bot.latency * 1000, 2)),
                        color=0xc8ff00)
  await ctx.response.send_message(embed=embed)


#kuji
@tree.command(name="kuji", description="おみくじを引きます")
async def kuji(ctx: discord.Interaction):
  omikuji_list = ["大大凶", "大凶", "凶", "末吉", "小吉", "中吉", "吉", "大吉", "大大吉"]
  await ctx.response.send_message('今日の運勢は...** ' + random.choice(omikuji_list) + '**！')


#userinfo
@tree.command(name="userinfo", description="ユーザー情報を取得します")
@discord.app_commands.describe(user="ユーザーをメンションまたはユーザーIDで指定")
async def userinfo(ctx: discord.Interaction, user:str):
  #メンションからID抽出
  target = re.sub("\\D", "", str(user))
  #ユーザーIDからユーザーを取得

  try:
    user = await client.fetch_user(target)
    #できなかったらエラー出す
  except:
    embed = discord.Embed(title=":x: エラー",
                          description="そのユーザーを取得できませんでした",
                          color=0xff0000)
    await ctx.response.send_message(embed=embed)

  else:
    embed = discord.Embed(title="ID",
                          description=target,
                          color=discord.Colour.green())
    try:
      embed.set_author(name=user, icon_url=user.avatar_url)
      embed.set_thumbnail(url=user.avatar_url)
    except:
      pass
    embed.add_field(name="表示名", value=user.display_name,inline=True)
    #embed.add_field(name="ID", value=user.id,inline=True)
    #embed.add_field(name="ステータス", value=user.status,inline=True)
    embed.add_field(name="メンション", value=user.mention, inline=True)
    embed.set_footer(text="アカウント作成日時: {0}".format(user.created_at))
    embed.set_thumbnail(url=user.avatar.url)
    await ctx.response.send_message(embed=embed)


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


#url
@tree.command(name="url", description="URLを短縮します")
@discord.app_commands.describe(url="URLを貼り付け")
async def url(ctx: discord.Interaction, url:str):
  req = requests.post(
    "https://ur7.cc/yourls-api.php?username=admin&password={0}&action=shorturl&format=json&url={1}"
    .format(os.environ['UR7'], url))

  r = req.json()

  try:
    short = json.dumps(r["shorturl"])

  except:
    embed = discord.Embed(title=":x: エラー",
                          description="エラーが発生しました。",
                          color=0xff0000)
    await ctx.response.send_message(embed=embed)

  else:
    embed = discord.Embed(title="短縮URL",
                          description="URLを短縮しました。\n[{0}]({0})".format(
                            short.strip('"')),
                          color=discord.Colour.green())
    embed.set_footer(text="Powered by UR7 Shortener")
    await ctx.response.send_message(embed=embed)

#youtubedl
@tree.command(name="ytdl", description="YouTube動画のダウンロードリンクを取得します")
@discord.app_commands.describe(url="動画URLを指定")
async def ytdl(ctx: discord.Interaction, url:str):
  await ctx.response.defer()
  
  youtube_dl_opts = {'format' : 'best'}

  try:
    with YoutubeDL(youtube_dl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        video_url = info_dict.get("url", None)
        video_title = info_dict.get('title', None)

  except:
    embed = discord.Embed(title=":x: エラー",
                          description="エラーが発生しました。",
                          color=0xff0000)
    await ctx.followup.send(embed=embed)

  else:
    embed = discord.Embed(title="YouTube動画ダウンロードリンク",description="`{0}`のダウンロードリンクを取得しました。\n\n[クリックしてダウンロード]({1})\n:warning: 著作権に違反してアップロードされた動画をダウンロードすることは違法です".format(video_title, video_url),color=discord.Colour.red())
    await ctx.followup.send(embed=embed)


#card
@tree.command(name="card", description="ユーザーカードを作成します")
async def card(ctx: discord.Interaction):
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

  song_title = "{0}".format(ctx.author.name)
  font_path = "BIZ-UDGothicR.ttc"
  font_size = 57
  font_color = (255, 255, 255)
  height = 105
  width = 330
  #img = add_text_to_image(base_img, song_title, font_path, font_size, font_color, height, width)

  base_img.paste(icon, (40, 40), icon)
  #base_img.add_text_to_image(base_img, song_title, font_path, font_size, font_color, height, width)
  base_img.save("test.png", format="png")
  await ctx.response.send_message(file=discord.File("test.png"))


#kick
'''@slash_client.slash(name="kick",
                    description="メンバーのキックをします",
                    options=[
                      create_option(name="user",
                                    description="ユーザーをメンションまたはユーザーIDで指定",
                                    option_type=3,
                                    required=True)
                    ])
#[create_option(name="user",description="ユーザーをメンションまたはユーザーIDで指定", option_type=3, required=True),create_option(name="reason",description="Kick理由", option_type=3, required=False)]
async def _slash_kick(ctx: SlashContext, user):
  #メンションからID抽出
  target = re.sub("\\D", "", str(user))
  #ユーザーIDからユーザーを取得

  #実行者に管理者権限があるか
  if not ctx.author.guild_permissions.administrator == True:
    embed = discord.Embed(title=":x: エラー",
                          description="あなたには管理者権限がないため、このコマンドを実行する権限がありません。",
                          color=0xff0000)
    await ctx.send(embed=embed)

  else:

    try:
      user = await bot.fetch_user(target)
      #できなかったらエラー出す
    except:
      embed = discord.Embed(title=":x: エラー",
                            description="そのユーザーを取得できませんでした",
                            color=0xff0000)
      await ctx.send(embed=embed)

    else:
      try:
        #await ctx.guild.kick(user, reason=reason)
        await ctx.guild.kick(user)
      except:
        embed = discord.Embed(title=":x: エラー",
                              description="そのユーザーをKickできません",
                              color=0xff0000)
        await ctx.send(embed=embed)
      else:
        embed = discord.Embed(title=":white_check_mark: 成功",
                              description="Kickが完了しました。\n",
                              timestamp=datetime.datetime.now(),
                              color=discord.Colour.green())
        try:
          embed.set_thumbnail(url=user.avatar_url)
        except:
          pass
        #if not reason:
        #    reason = "理由がありません"
        embed.add_field(name="**Kickされたユーザー**",
                        value="{0} [ID:{1}]".format(str(user), target),
                        inline=False)
        #embed.add_field(name="**理由**",value="{0}".format(str(reason),inline=False))
        embed.add_field(name="**実行者**",
                        value="{0}".format(str("<@!" + str(ctx.author.id) +
                                               ">"),
                                           inline=False))
        await ctx.send(embed=embed)


#ban
@slash_client.slash(name="ban",
                    description="メンバーのBANをします",
                    options=[
                      create_option(name="user",
                                    description="ユーザーをメンションまたはユーザーIDで指定",
                                    option_type=3,
                                    required=True)
                    ])
async def _slash_ban(ctx: SlashContext, user):
  #メンションからID抽出
  target = re.sub("\\D", "", str(user))
  #ユーザーIDからユーザーを取得

  #実行者に管理者権限があるか
  if not ctx.author.guild_permissions.administrator == True:
    embed = discord.Embed(title=":x: エラー",
                          description="あなたには管理者権限がないため、このコマンドを実行する権限がありません。",
                          color=0xff0000)
    await ctx.send(embed=embed)

  else:

    try:
      user = await bot.fetch_user(target)
      #できなかったらエラー出す
    except:
      embed = discord.Embed(title=":x: エラー",
                            description="そのユーザーを取得できませんでした",
                            color=0xff0000)
      await ctx.send(embed=embed)

    else:
      try:
        await ctx.guild.ban(user,
                            reason="{0}さんによってBANが実行されました".format(
                              ctx.author.id),
                            delete_message_days=0)
      except:
        embed = discord.Embed(title=":x: エラー",
                              description="そのユーザーをBANできません",
                              color=0xff0000)
        await ctx.send(embed=embed)
      else:
        embed = discord.Embed(title=":white_check_mark: 成功",
                              description="BANが完了しました。\n",
                              timestamp=datetime.datetime.now(),
                              color=discord.Colour.green())
        try:
          embed.set_thumbnail(url=user.avatar_url)
        except:
          pass
        #if not reason:
        #    reason = "理由がありません"
        embed.add_field(name="**BANされたユーザー**",
                        value="{0} [ID:{1}]".format(
                          str("<@!" + str(target) + ">"), target),
                        inline=False)
        #embed.add_field(name="**理由**",value="{0}".format(str(reason),inline=False))
        embed.add_field(name="**実行者**",
                        value="{0}".format(str("<@!" + str(ctx.author.id) +
                                               ">"),
                                           inline=False))
        await ctx.send(embed=embed)
'''

#unban
@tree.command(name="unban",description="ユーザーのBAN解除をします")
@discord.app_commands.describe(user="ユーザーをメンションまたはユーザーIDで指定")
async def unban(ctx: discord.Interaction, user:str):
  #メンションからID抽出
  target = re.sub("\\D", "", str(user))
  #ユーザーIDからユーザーを取得

  #実行者に管理者権限があるか
  if not ctx.user.guild_permissions.administrator == True:
    embed = discord.Embed(title=":x: エラー",
                          description="あなたには管理者権限がないため、このコマンドを実行する権限がありません。",
                          color=0xff0000)
    await ctx.response.send_message(embed=embed)

  else:

    try:
      user = await client.fetch_user(target)
      #できなかったらエラー出す
    except:
      embed = discord.Embed(title=":x: エラー",
                            description="そのユーザーを取得できませんでした",
                            color=0xff0000)
      await ctx.response.send_message(embed=embed)

    else:
      try:
        await ctx.guild.unban(user)
      except:
        embed = discord.Embed(title=":x: エラー",
                              description="そのユーザーをBAN解除できません",
                              color=0xff0000)
        await ctx.response.send_message(embed=embed)
      else:
        embed = discord.Embed(title=":white_check_mark: 成功",
                              description="BAN解除が完了しました。\n",
                              timestamp=datetime.datetime.now(),
                              color=discord.Colour.green())
        try:
          embed.set_thumbnail(url=user.avatar_url)
        except:
          pass
        #if not reason:
        #    reason = "理由がありません"
        embed.add_field(name="**BAN解除されたユーザー**",
                        value="{0} [ID:{1}]".format(str(user), target),
                        inline=False)
        #embed.add_field(name="**理由**",value="{0}".format(str(reason),inline=False))
        embed.add_field(name="**実行者**",
                        value="{0}".format(str("<@!" + str(ctx.author.id) +
                                               ">"),
                                           inline=False))
        await ctx.response.send_message(embed=embed)


#delete
@tree.command(name="delete",description="メッセージを削除します")
@discord.app_commands.describe(num="削除件数を指定")
async def delete(ctx: discord.Interaction, num:int):

  #実行者に管理者権限があるか
  if not ctx.user.guild_permissions.administrator == True:
    embed = discord.Embed(title=":x: エラー",
                          description="あなたには管理者権限がないため、このコマンドを実行する権限がありません。",
                          color=0xff0000)
    await ctx.response.send_message(embed=embed)

  else:
    channel = ctx.channel
    now = datetime.datetime.now()
    await ctx.response.defer()
    try:
      deleted = await channel.purge(before=now, limit=int(num), reason=f'{ctx.user}によるコマンド実行')

    except:
      embed = discord.Embed(title=":x: エラー",
                            description="エラーが発生しました",
                            color=0xff0000)
      await ctx.followup.send(embed=embed)

    else:
      embed = discord.Embed(title=":white_check_mark: 成功",
                            description="`{0}`メッセージを削除しました".format(
                              len(deleted)),
                            color=discord.Colour.green())
      await ctx.followup.send(embed=embed)


#Google検索
@tree.command(name="search",description="Google検索をします")
@discord.app_commands.describe(word="検索語句を指定")
async def search(ctx: discord.Interaction, word:str):
  await ctx.response.defer()
  start = time.time()
  searched = []
  #g_url = 'https://www.google.co.jp/search'
  count = 0
  for url in GoogleSearch().search(word, lang="jp", num=3):
    searched.append(url)
    count += 1
    if (count == 3):
      stop = time.time()
      embed = discord.Embed(title="検索結果",
                            description=":one: " + searched[0] + "\n:two: " +
                            searched[1] + "\n:three: " + searched[2])
      await ctx.followup.send(content="検索しました（{0}秒）".format(stop - start),
                             embed=embed)
      break


#GuildIcon
@tree.command(name="getguildicon", description="このサーバーのアイコンを取得します")
async def getguildicon(ctx: discord.Interaction):
  try:
    guildicon = ctx.guild.icon.replace(static_format='png')
  except:
    embed = discord.Embed(title=":x: エラー",
                          description="サーバーアイコンを取得できません",
                          color=0xff0000)
    await ctx.response.send_message(embed=embed)
  else:
    embed = discord.Embed(title="サーバーアイコン",
                          description=":white_check_mark:画像を取得しました。")
    embed.set_thumbnail(url=guildicon)
    await ctx.response.send_message(embed=embed)


#YouTube Together
@tree.command(name="youtube", description="ボイスチャンネルでYouTubeの再生を開始します")
async def youtube(ctx: discord.Interaction):
  try:
    link = await bot.togetherControl.create_link(ctx.author.voice.channel.id,
                                                 'youtube',
                                                 max_age=86400)
  except:
    embed = discord.Embed(title=":x: エラー",
                          description="ボイスチャンネルに参加してください",
                          color=0xff0000)
    await ctx.response.send_message(embed=embed)
  else:
    embed = discord.Embed(
      title="YouTube",
      description="[クリック]({0})して開始！\n※二人目以降の方は押す必要はありません".format(link),
      color=discord.Colour.red())
    await ctx.response.send_message(embed=embed)


#Putt Party
@tree.command(name="putt-party",
                    description="ボイスチャンネルでPutt Partyを開始します（Nitro Boostユーザー限定）")
async def puttparty(ctx: discord.Interaction):
  try:
    link = await bot.togetherControl.create_link(ctx.author.voice.channel.id,
                                                 'putt-party',
                                                 max_age=86400)
  except:
    embed = discord.Embed(title=":x: エラー",
                          description="ボイスチャンネルに参加してください",
                          color=0xff0000)
    await ctx.response.send_message(embed=embed)
  else:
    embed = discord.Embed(
      title="Putt Party",
      description=
      "[クリック]({0})して開始！\n認証画面が表示されたら、認証ボタンをクリックして下さい。\n※二人目以降の方は押す必要はありません\n※Nitro Boostユーザーのみご利用できます"
      .format(link),
      color=0x90ee90)
    await ctx.response.send_message(embed=embed)


#Poker Night
@tree.command(
  name="poker-night",
  description="ボイスチャンネルでPoker Nightを開始します（Nitro Boostユーザー限定・18歳以上）")
async def pokernight(ctx: discord.Interaction):
  try:
    link = await bot.togetherControl.create_link(ctx.author.voice.channel.id,
                                                 'poker',
                                                 max_age=86400)
  except:
    embed = discord.Embed(title=":x: エラー",
                          description="ボイスチャンネルに参加してください",
                          color=0xff0000)
    await ctx.response.send_message(embed=embed)
  else:
    embed = discord.Embed(
      title="Poker Night",
      description=
      "[クリック]({0})して開始！\n認証画面が表示されたら、認証ボタンをクリックして下さい。\n※二人目以降の方は押す必要はありません\n※Nitro Boostユーザーのみご利用できます\n※18歳以上の方のみご利用できます"
      .format(link),
      color=discord.Colour.dark_blue())
    await ctx.response.send_message(embed=embed)


#Sketch Heads
@tree.command(
  name="sketch-heads",
  description="ボイスチャンネルでSketch Headsを開始します（Nitro Boostユーザー限定）")
async def sketchheads(ctx: discord.Interaction):
  try:
    link = await bot.togetherControl.create_link(ctx.author.voice.channel.id,
                                                 'sketch-heads',
                                                 max_age=86400)
  except:
    embed = discord.Embed(title=":x: エラー",
                          description="ボイスチャンネルに参加してください",
                          color=0xff0000)
    await ctx.response.send_message(embed=embed)
  else:
    embed = discord.Embed(
      title="Sketch Heads",
      description=
      "[クリック]({0})して開始！\n認証画面が表示されたら、認証ボタンをクリックして下さい。\n※二人目以降の方は押す必要はありません\n※Nitro Boostユーザーのみご利用できます"
      .format(link),
      color=0x483d8b)
    await ctx.response.send_message(embed=embed)


#Chess
@tree.command(
  name="chess",
  description="ボイスチャンネルでChess in the Parkを開始します（Nitro Boostユーザー限定）")
async def chess(ctx: discord.Interaction):
  try:
    link = await bot.togetherControl.create_link(ctx.author.voice.channel.id,
                                                 'chess',
                                                 max_age=86400)
  except:
    embed = discord.Embed(title=":x: エラー",
                          description="ボイスチャンネルに参加してください",
                          color=0xff0000)
    await ctx.response.send_message(embed=embed)
  else:
    embed = discord.Embed(
      title="Chess in the Park",
      description=
      "[クリック]({0})して開始！\n認証画面が表示されたら、認証ボタンをクリックして下さい。\n※二人目以降の方は押す必要はありません".
      format(link),
      color=discord.Colour.dark_green())
    await ctx.response.send_message(embed=embed)


#Blazing 8s
@tree.command(name="blazing-8s",
                    description="ボイスチャンネルでBlazing 8sを開始します（Nitro Boostユーザー限定）")
async def blazing8s(ctx: discord.Interaction):
  try:
    link = await bot.togetherControl.create_link(ctx.author.voice.channel.id,
                                                 'blazing-8s',
                                                 max_age=86400)
  except:
    embed = discord.Embed(title=":x: エラー",
                          description="ボイスチャンネルに参加してください",
                          color=0xff0000)
    await ctx.response.send_message(embed=embed)
  else:
    embed = discord.Embed(
      title="Blazing 8s",
      description=
      "[クリック]({0})して開始！\n認証画面が表示されたら、認証ボタンをクリックして下さい。\n※二人目以降の方は押す必要はありません\n※Nitro Boostユーザーのみご利用できます"
      .format(link),
      color=0xcd5c5c)
    await ctx.response.send_message(embed=embed)


#Letter League
@tree.command(
  name="letter-league",
  description="ボイスチャンネルでLetter Leagueを開始します（Nitro Boostユーザー限定）")
async def letterleague(ctx: discord.Interaction):
  try:
    link = await bot.togetherControl.create_link(ctx.author.voice.channel.id,
                                                 'letter-league',
                                                 max_age=86400)
  except:
    embed = discord.Embed(title=":x: エラー",
                          description="ボイスチャンネルに参加してください",
                          color=0xff0000)
    await ctx.response.send_message(embed=embed)
  else:
    embed = discord.Embed(
      title="Letter League",
      description=
      "[クリック]({0})して開始！\n認証画面が表示されたら、認証ボタンをクリックして下さい。\n※二人目以降の方は押す必要はありません\n※Nitro Boostユーザーのみご利用できます"
      .format(link),
      color=0xf5deb3)
    await ctx.response.send_message(embed=embed)


#Checkers in the Park
@tree.command(
  name="checkers",
  description="ボイスチャンネルでCheckers in the Parkを開始します（Nitro Boostユーザー限定）")
async def checkers(ctx: discord.Interaction):
  try:
    link = await bot.togetherControl.create_link(ctx.author.voice.channel.id,
                                                 'checkers',
                                                 max_age=86400)
  except:
    embed = discord.Embed(title=":x: エラー",
                          description="ボイスチャンネルに参加してください",
                          color=0xff0000)
    await ctx.response.send_message(embed=embed)
  else:
    embed = discord.Embed(
      title="Checkers in the Park	",
      description=
      "[クリック]({0})して開始！\n認証画面が表示されたら、認証ボタンをクリックして下さい。\n※二人目以降の方は押す必要はありません\n※Nitro Boostユーザーのみご利用できます"
      .format(link),
      color=0x2f4f4f)
    await ctx.response.send_message(embed=embed)


#SpellCast
@tree.command(name="spellcast",
                    description="ボイスチャンネルでSpellCastを開始します（Nitro Boostユーザー限定）")
async def spellcast(ctx: discord.Interaction):
  try:
    link = await bot.togetherControl.create_link(ctx.author.voice.channel.id,
                                                 'spellcast',
                                                 max_age=86400)
  except:
    embed = discord.Embed(title=":x: エラー",
                          description="ボイスチャンネルに参加してください",
                          color=0xff0000)
    await ctx.response.send_message(embed=embed)
  else:
    embed = discord.Embed(
      title="SpellCast",
      description=
      "[クリック]({0})して開始！\n認証画面が表示されたら、認証ボタンをクリックして下さい。\n※二人目以降の方は押す必要はありません\n※Nitro Boostユーザーのみご利用できます"
      .format(link),
      color=0x1e90ff)
    await ctx.response.send_message(embed=embed)


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


@client.event
async def on_message(message):
  if message.author.bot:
    return

  if message.content == "せやな":
    #i = random.choice([0, 1])

    await message.channel.send("<:Seyana:851104856110399488>")

  if message.channel.name == "akane-talk":
    reps = [
      "あ ほ く さ", "あほくさ", "せやな", "あれな", "ええで", "ええんちゃう？", "ほんま", "知らんがな",
      "知らんけど～", "それな", "そやな", "わかる", "なんや", "うん", "どしたん？", "やめたら？そのゲーム", "な。",
      "うん？", "わかる（感銘）", "わかる（天下無双）", "マ？", "Sorena...", "はよ", "Seyana...",
      "や↑ったぜ", "なに買って来たん？", "ほかには？", "そぉい！", "ウマいやろ？", ""
    ]
    i = random.choice(reps)
    await message.channel.send(i)

#全てのインタラクションを取得
@client.event
async def on_interaction(ctx: discord.Interaction):
    try:
        if ctx.data['component_type'] == 2:
            await on_button_click(ctx)
    except KeyError:
        pass


#Buttonの処理
async def on_button_click(ctx: discord.Interaction):
    custom_id = ctx.data["custom_id"]
  
    if custom_id == "j_g":
      result = random.choice(range(1,3))

      if result == 1:
        await ctx.response.send_message("ぽん✌\n君の勝ちやで～")

      elif result == 2:
        await ctx.response.send_message("ぽん✊\nあいこやな。")
        
      else:
        await ctx.response.send_message("ぽん✋\n私の勝ちやな。また挑戦してや。")

    if custom_id == "j_c":
      result = random.choice(range(1,3))

      if result == 1:
        await ctx.response.send_message("ぽん✋\n君の勝ちやで～")

      elif result == 2:
        await ctx.response.send_message("ぽん✌\nあいこやな。")
        
      else:
        await ctx.response.send_message("ぽん✊\n私の勝ちやな。また挑戦してや。")

    if custom_id == "j_p":
      result = random.choice(range(1,3))

      if result == 1:
        await ctx.response.send_message("ぽん✊\n君の勝ちやで～")

      elif result == 2:
        await ctx.response.send_message("ぽん✋\nあいこやな。")
        
      else:
        await ctx.response.send_message("ぽん✌\n私の勝ちやな。また挑戦してや。")


keep_alive()

#Botの起動とDiscordサーバーへの接続
#429エラー防止
try:
  client.run(TOKEN)

except:
  os.system("kill 1")
