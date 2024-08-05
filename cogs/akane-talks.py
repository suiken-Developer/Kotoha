import random

import discord
from discord import app_commands
from discord.ext import commands  # Bot Commands Frameworkをインポート


##################################################

''' コマンド '''


class Akane_talks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Cog読み込み時
    @commands.Cog.listener()
    async def on_ready(self):
        print("akane-talksCog on ready")


    #########################


    '''
    # せやな
    @commands.Cog.listener("on_message")
    async def seyana(self, message):
        if message.author.bot or message.mention_everyone:
            return
        
        elif message.content == "せやな":
            await message.channel.send("<:Seyana:851104856110399488>")
    '''

        
    # #akane-talk
    @commands.Cog.listener("on_message")
    async def talk(self, message):
        if message.author.bot or message.mention_everyone:
            return
        
        elif message.guild:
            if message.channel.name == "akane-talk":
                reps = [
                    "あ ほ く さ", "あほくさ", "せやな", "あれな",
                    "ええで", "ええんちゃう？", "ほんま", "知らんがな",
                    "知らんけど～", "それな", "そやな", "わかる", "なんや",
                    "うん", "どしたん？", "やめたら？そのゲーム", "な。",
                    "うん？", "わかる（感銘）", "わかる（天下無双）",
                    "マ？", "Sorena...", "はよ", "Seyana...",
                    "や↑ったぜ", "なに買って来たん？", "ほかには？",
                    "そぉい！", "ウマいやろ？",
                ]
                i = random.choice(reps)
                await message.channel.send(i)


    #########################

    # エラー出力
    async def cog_command_error(self, ctx: discord.Interaction, error):
        embed = discord.Embed(title="エラー",
                              description="不明なエラーが発生しました。",
                              color=0xff0000)
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Akane_talks(bot))