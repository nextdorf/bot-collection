try:
  from common.utils import *
except:
  import common
  from utils import *
import datetime
import pytz
import random
import re

from twitchio import Message
from twitchio.ext import commands
from obs_server import *
from pathlib import Path

buggyPastaConfig = botConfig['Twitch']['BuggyPasta']

# print(obsVideoCommandIntoToml({'test': ObsVideoCommand('new_video', -12, 'videos/lol.webm', Rect(0, 320, 300, 0), Vec2(728, 285.0), Vec2(-0.56, 0.56))}))


class Bot(commands.Bot):
  def __init__(self, botUser: str, channels=[]):
    # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
    # prefix can be a callable, which returns a list of strings or a string...
    # initial_channels can also be a callable which returns a list of strings...
    self.botUserConfig: twitchUserEntry = buggyPastaConfig[botUser]
    self.botUserConfig.apply(
      lambda token: super(Bot, self).__init__(token=token, prefix='!', initial_channels=channels)
      )
    self.obs = ObsClient()
    self.videoCommands: dict[str, ObsVideoCommand] = {}


  async def event_ready(self):
    print(f'Logged in as | {self.nick}')
    print(f'User id is | {self.user_id}')

  async def update_obs_commands(self, obsCommands: dict[str, ObsVideoCommand], appendOnly: bool):
    if appendOnly:
      keys = list(self.videoCommands.keys())
      for cmdName in keys:
        if cmdName in obsCommands:
          self.remove_command(cmdName)
    else:
      for cmdName in self.videoCommands:
        self.remove_command(cmdName)
      self.videoCommands.clear()
    for (cmdName, cmdArgs) in obsCommands.items():
      self.videoCommands[cmdName] = cmdArgs
      def getCmdFunc(videoName: str, cmdArgs: ObsVideoCommand):
        arr = [videoName]
        cmdArgs = cmdArgs
        async def inner(ctx: commands.Context):
          videoName = arr[0]
          print(repr(videoName))
          videoName = videoName.lower()
          crop: Rect = cmdArgs.cropRect
          pos: Vec2 = cmdArgs.position
          scale: Vec2 = cmdArgs.scale
          transformation = dict(
            cropBottom = crop.bottom,
            cropLeft = crop.left,
            cropRight = crop.right,
            cropTop = crop.top,
            positionX = pos.x,
            positionY = pos.y,
            scaleX = scale.x,
            scaleY = scale.y,
          )
          await bot.obs.startVideo(cmdArgs.sourceName, cmdArgs.volumeInDb, cmdArgs.path, transformation)
        return inner
      cmd = commands.Command(cmdName, getCmdFunc(cmdName, cmdArgs))
      self.add_command(cmd)


bot = Bot('buggynoodles', ['NextBigIdea'])

@bot.command(aliases=['bot'])
async def bothelp(ctx: commands.Context, *cmds: str):
  allCmds = dict(
    ping = 'Check ob ich da bin',
    discord = 'Invitation f??r discord',
    project = 'Das aktuelle Projekt',
    time = 'Aktuelle Zeit bei mir oder in einer Zeitzone ("!time Asia/Tokyo", "!time UTC", ..)',
    image = 'Blendet ein Bild in Obs ein, siehe "!image list"',
    video = 'Spielt kurzes Video ab, siehe "!video list"',
    bot = 'Dieser Hilfetext',
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
  await ctx.send(f'Ich versuche einen Videoeditor in Rust ???? zu schreiben, der frei und open source ist. Dazu benutze ich FFMPEG zum editieren, egui f??r die UI und Vulkan (bzw WGPU) f??r das Rendern.Da ich noch Anf??nger in Rust bin, ist Backseating erw??nscht ImTyping')

@bot.command(aliases=['dc', 'd'])
async def discord(ctx: commands.Context):
  await ctx.send('https://discord.gg/tUPJrMm9Mw')

@bot.command()
async def github(ctx: commands.Context):
  await ctx.send('https://github.com/nextdorf')

@bot.command()
async def time(ctx: commands.Context, *tzs: str):
  if tzs:
    for tz in tzs:
      try:
        time = datetime.datetime.now(pytz.timezone(tz)).strftime('%H:%M:%S Uhr.')
      except:
        time = '??\_(???)_/??'
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
async def video(ctx: commands.Context, subcmd:str=''):
  subcmd = subcmd.strip().lower()
  print(ctx.message)
  if subcmd == 'list':
    videoCmds = list(toml.load('obs_videos_test.toml').keys())
    knownCmds = ' '.join(videoCmds)
    await ctx.send(f'{knownCmds}')
  elif subcmd == 'update':
    if ctx.author.is_broadcaster or ctx.author.is_mod:
      with open('obs_videos_test.toml', 'r') as f:
        data = obsVideoCommandsFromToml(f.read())
        await bot.update_obs_commands(data, False)
    else:
      await ctx.send(f'@{ctx.author.name} is not in the sudoers file! This incident will be reported!')
  else:
    await ctx.send(f'@{ctx.author.name} "{subcmd}" nicht in Liste bekannter Commands: list | update')



asyncio.run(botConfig['Obs'].apply(bot.obs)(subscriptions=EventSubscription.MediaInputs))
with open('obs_videos_test.toml', 'r') as f:
  data = obsVideoCommandsFromToml(f.read())
  asyncio.run(bot.update_obs_commands(data, False))
bot.obs.addAsyncioTask()
bot.run()
# bot.run() is blocking and will stop execution of any below code here until stopped or closed.






