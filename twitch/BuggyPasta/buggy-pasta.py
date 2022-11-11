try:
  from common.utils import *
except:
  import common
  from utils import *
import datetime
import pytz
import random

from twitchio.ext import commands

buggyPastaConfig = botConfig['Twitch']['BuggyPasta']

class Bot(commands.Bot):
  def __init__(self, botUser: str, channels=[]):
    # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
    # prefix can be a callable, which returns a list of strings or a string...
    # initial_channels can also be a callable which returns a list of strings...
    self.botUserConfig: twitchUserEntry = buggyPastaConfig[botUser]
    self.botUserConfig.apply(
      lambda token: super(Bot, self).__init__(token=token, prefix='!', initial_channels=channels)
      )

  async def event_ready(self):
    print(f'Logged in as | {self.nick}')
    print(f'User id is | {self.user_id}')

bot = Bot('buggynoodles', ['NextBigIdea'])

@bot.command()
async def ping(ctx: commands.Context):
  await ctx.send(f'Pong {ctx.author.name}!')

@bot.command(aliases=['p'])
async def project(ctx: commands.Context):
  await ctx.send(f'Ich versuche einen Videoeditor in Rust 🦀 zu schreiben, der frei und open source ist. Dazu benutze ich FFMPEG zum editieren, egui für die UI und Vulkan (bzw WGPU) für das Rendern.Da ich noch Anfänger in Rust bin, ist Backseating erwünscht ImTyping')

@bot.command()
async def time(ctx: commands.Context, *tzs: str):
  if tzs:
    for tz in tzs:
      try:
        time = datetime.datetime.now(pytz.timezone(tz)).strftime('%H:%M:%S Uhr.')
      except:
        time = '¯\_(ツ)_/¯'
      await ctx.send(f'{tz}: {time}')

  else:
    if random.random() < .15:
      time = 'Haut vor Knochen Kappa'
    else:
      time = datetime.datetime.now().strftime('%H:%M:%S Uhr.')
    await ctx.send(f'@{ctx.author.name} Bei mir ist gerade {time}')


bot.run()
# bot.run() is blocking and will stop execution of any below code here until stopped or closed.






