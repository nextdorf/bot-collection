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
import nest_asyncio
nest_asyncio.apply() #Wichtig für Jupyter Notebook
import asyncio

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

if False and __name__ == '__main__':
  runner = botConfig['Discord']['BuggyPasta'].apply(bot, run_async=False)
  runner(log_handler=handler, log_level=logging.DEBUG)
else:
  runner = botConfig['Discord']['BuggyPasta'].apply(bot, run_async=True)
  async def runOnce():
    videoCmdChannel = next((ch for ch in bot.get_all_channels() if ch.name=='video-commands' and isinstance(ch, discord.TextChannel)), None)

    msgs = [m async for m in videoCmdChannel.history()]
    # await bot.close()
    return msgs

  asyncio.get_event_loop().create_task(runner())
  videoCmdChannel = next((ch for ch in bot.get_all_channels() if ch.name=='video-commands' and isinstance(ch, discord.TextChannel)), None)
  msgs = asyncio.run(runOnce())
  msg0 = msgs[-1]
  msg0.content
  msg0.reactions
  isApproved = next((True for r in msg0.reactions if r.emoji.name == 'approved'), False)
