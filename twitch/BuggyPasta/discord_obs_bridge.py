try:
  from common.utils import *
except:
  import common
  from utils import *

import discord
from discord.ext.commands import Bot, Context
from discord import Message
import nest_asyncio
nest_asyncio.apply() #Wichtig für Jupyter Notebook
import asyncio
from pathlib import Path


class videoCommandHandle:
  def __init__(self, channel:discord.TextChannel, media_dir:Path|str='discord_media', config_file:Path|str='obs_videos.toml') -> None:
    self.channel = channel
    if not isinstance(media_dir, Path): media_dir = Path(media_dir)
    if not media_dir.is_dir(): media_dir = None
    self.media_dir = media_dir
    if not isinstance(config_file, Path): config_file = Path(config_file)
    if not config_file.is_file() : config_file = None
    self.config_file = config_file

  # async def insert(self, newCmdKey:str, newCmdVal: 'ObsVideoCommand', cmds: dict[str, 'ObsVideoCommand']|None=None):
  #   if cmds is None:
  #     with open(str(self.config_file), 'r') as f:
  #       cmds = obsVideoCommandsFromToml(f.read())
  #   was_updated = False
  #   if newCmdVal.message_id is not None:
  #     if newCmdKey in cmds:
  #       oldCmdVal = cmds[newCmdKey]
  #       sameId = oldCmdVal.message_id == newCmdVal.message_id
  #       sameSubmitter = oldCmdVal.submitter == newCmdVal.submitter or oldCmdVal.submitter_twitch == newCmdVal.submitter_twitch
  #       canOverwrite = sameSubmitter or sameId
  #       oldmsg = None
  #       if not canOverwrite and oldCmdVal.message_id is not None:
  #         oldmsg = await self.channel.fetch_message(oldCmdVal.message_id)
  #         approvalReaction = ((r for r in oldmsg.reactions if isinstance(r, discord.Emoji) and r.name == 'approved'), None)
  #         isApproved = approvalReaction is not None
  #         if not isApproved:
  #           canOverwrite = True
  #       if not canOverwrite:
  #         newmsg = await self.channel.fetch_message(newCmdVal.message_id)
  #         approvalReaction = ((r for r in newmsg.reactions if isinstance(r, discord.Emoji) and r.name == 'approved'), None)
  #         isApproved = approvalReaction is not None
  #         if isApproved:
  #           newmsgRepr = f'Msg[created at {newmsg.created_at} by {newmsg.author}]'
  #           oldmsgRepr = f'Msg[created at {oldmsg.created_at} by {oldmsg.author}]' if oldmsg is not None else 'Msg[No metadata]'
  #           raise ValueError(f'Cannot overwrite "{newCmdKey}": {newmsgRepr} --> {oldmsgRepr}')
  #       if canOverwrite:
  #         oldCmdValDict = obsVideoCommandsIntoDict(oldCmdVal)
  #         newCmdValDict0 = obsVideoCommandsIntoDict(newCmdVal)
  #         newCmdVal1 = obsVideoCommandsFromDict(newCmdVal, )
  #         was_updated = True
  #   return cmds, was_updated

  async def handleMessage(self, message_id: int, cmds: dict[str, 'ObsVideoCommand']|None=None):
    if cmds is None:
      with open(str(self.config_file), 'r') as f:
        cmds = obsVideoCommandsFromToml(f.read())
    was_updated = False
    (oldMsgKey, oldMsgCmd) = next(((k, v) for k, v in cmds.items() if v.message_id==message_id), (None, None))

    msg = await self.channel.fetch_message(message_id)
    submitter = msg.author.display_name
    createdAt = msg.created_at
    timestamp = msg.edited_at if msg.edited_at else createdAt
    approvalReaction = next((r for r in msg.reactions if isinstance(r.emoji, discord.Emoji) and r.emoji.name == 'approved'), None)
    approvalReaction.
    isApproved = approvalReaction is not None
    if isApproved:
      if oldMsgCmd is not None:
        if timestamp == oldMsgCmd.message_timestamp:
          return cmds, was_updated
    else:
      return cmds, was_updated

    attachment = msg.attachments[0] if len(msg.attachments) == 1 else 
    #TODO: Fix this mess!!!





intents = discord.Intents.default()

intents.message_content = True
bot = Bot(command_prefix='!', intents=intents)

@bot.command()
async def ping(ctx: Context):
  await ctx.send('pong (Twitchbot)')


@bot.listen()
async def on_message(msg: Message):
  if msg.author.id == bot.user.id:
    return
  s = msg.content.lower()



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
msg0.activity
print(msg0.id, 'https://discord.com/channels/1039221680054214746/1047262752604958790/1047267620518375425')
msg0.content
msg0.reactions
approvalReaction = next((r for r in msg0.reactions if r.emoji.name == 'approved'), None)
isApproved = approvalReaction is not None

pins = asyncio.run(videoCmdChannel.pins())
pin0 = pins[0]
pin0.reference


timestamp = msg0.created_at if msg0.edited_at is None else msg0.edited_at
media = msg0.attachments[0]
asyncio.run(media.save(Path('discord_media/lol.webm')))



