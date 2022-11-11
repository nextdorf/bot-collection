try:
  from common.utils import *
except:
  import common
  from utils import *

from ascii_art import *
from cowsay_cmd import Cowsay
import logging

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

import discord
from discord.ext.commands import Bot, Context
from discord import Message

# intents = discord.Intents._from_value(534723950661)
# intents = discord.Intents._from_value(1632088094789)
intents = discord.Intents.default()

intents.message_content = True
bot = Bot(command_prefix='!', intents=intents)
cowsayObj = Cowsay()

@bot.command()
async def ping(ctx: Context):
  await ctx.send('pong')

@bot.command()
async def add(ctx: Context, *x:int):
  await ctx.send(sum(x) if len(x)>0 else 0)

@bot.command()
async def addS(ctx: Context, *x:str):
  await ctx.send(''.join(x))

#cowsay.addCommandsToBot(bot)
@bot.command()
async def cowsay(ctx: Context, *args: str):
  await cowsayObj.cowcom(ctx, *args, cowcommand='cowsay')
@bot.command()
async def cowthink(ctx: Context, *args: str):
  await cowsayObj.cowcom(ctx, *args, cowcommand='cowthink')

@bot.listen()
async def on_message(msg: Message):
  if msg.author.id == bot.user.id:
    return
  s = msg.content.lower()
  if s.find('arch btw')>=0:
    await msg.reply(f'```{ascii_logos["arch"]}```')

runner = botConfig.apply('Discord', 'BuggyPasta', bot)
runner(log_handler=handler, log_level=logging.DEBUG)
