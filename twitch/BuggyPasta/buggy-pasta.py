try:
  from common.utils import *
except:
  import common
  from utils import *
import datetime
import pytz
import random
import re

from twitchio.ext import commands
from obs_server2 import *
from pathlib import Path

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
    self.obs = ObsServer()


  async def event_ready(self):
    print(f'Logged in as | {self.nick}')
    print(f'User id is | {self.user_id}')

bot = Bot('buggynoodles', ['NextBigIdea'])

@bot.command(aliases=['h'])
async def help(ctx: commands.Context, *cmds: str):
  allCmds = dict(
    ping = 'Check ob ich da bin',
    discord = 'Invitation für discord',
    project = 'Das aktuelle Projekt',
    time = 'Aktuelle Zeit bei mir oder in einer Zeitzone ("!time Asia/Tokyo", "!time UTC", ..)',
    image = 'Blendet ein Bild in Obs ein, siehe "!image list"',
    video = 'Spielt kurzes Video ab, siehe "!video list"',
    help = 'Dieser Hilfetext',
  )
  validCmds = list({c for c in cmds if c in allCmds})
  invalidCmds = list({c for c in cmds if c not in allCmds})
  if not cmds:
    validCmds = list(allCmds)
  if validCmds:
    await ctx.send(' | '.join([f'{k}: {allCmds[k]}' for k in validCmds]))
  if invalidCmds:
    await ctx.send('Es existiert kein Hilfetext zu: ' + ', '.join(invalidCmds))

@bot.command()
async def ping(ctx: commands.Context):
  await ctx.send(f'Pong {ctx.author.name}!')

@bot.command(aliases=['p'])
async def project(ctx: commands.Context):
  await ctx.send(f'Ich versuche einen Videoeditor in Rust 🦀 zu schreiben, der frei und open source ist. Dazu benutze ich FFMPEG zum editieren, egui für die UI und Vulkan (bzw WGPU) für das Rendern.Da ich noch Anfänger in Rust bin, ist Backseating erwünscht ImTyping')

@bot.command(aliases=['dc', 'd'])
async def discord(ctx: commands.Context):
  await ctx.send('https://discord.gg/tUPJrMm9Mw')

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

@bot.command()
async def image(ctx: commands.Context, imgName:str=''):
  print(repr(imgName))
  regex = re.fullmatch('[\w ]*', imgName if imgName else '')
  if not regex: return
  imgName = imgName.lower()
  if imgName.lower() == 'list':
    imgs = [p.stem for p in Path('images').glob('*')]
    knownImgs = '"%s"' % ('", "'.join(imgs))
    await ctx.send(f'@{ctx.author.name}, ich kenne: {knownImgs}')
    return
  if imgName:
    paths = list(Path('images').glob(f'{imgName}.*'))
    if paths:
      path = paths[0]
    else:
      return
  else:
    path = None
  await bot.obs.changeImage('Screen', 'Image', path, None, 400)

@bot.command()
async def video(ctx: commands.Context, videoName:str=''):
  print(repr(videoName))
  regex = re.fullmatch('[\w ]*', videoName if videoName else '')
  if not regex: return
  videoName = videoName.lower()
  if videoName.lower() == 'list':
    imgs = [p.stem for p in Path('videos').glob('*')]
    knownImgs = '"%s"' % ('", "'.join(imgs))
    await ctx.send(f'@{ctx.author.name}, ich kenne: {knownImgs}')
    return
  await bot.obs.restartVideo('Screen', videoName)

asyncio.run(botConfig['Obs'].apply(bot.obs)(subscriptions=0))
bot.run()
# bot.run() is blocking and will stop execution of any below code here until stopped or closed.






