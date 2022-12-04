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


def getCodeBlock(s:str):
  if s.startswith('```'):
    idxStart = 0
  else:
    idxStart = s.find('\n```')+1
    if idxStart == 0:
      return None
  idxStart+=3
  if s[idxStart:].lower().startswith('toml'):
    idxStart += 4
  idxEnd = s.find('```', idxStart)
  if idxEnd < 0:
    return None
  return s[idxStart: idxEnd]

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

  async def removeApproval(self, approvalReaction: discord.Reaction):
    if approvalReaction is None:
      return
    async for user in approvalReaction.users():
      await approvalReaction.remove(user)

  async def handleMessage(self, message_id: int, cmds: dict[str, 'ObsVideoCommand']|None=None):
    if cmds is None:
      with open(str(self.config_file), 'r') as f:
        cmds = obsVideoCommandsFromToml(f.read())
    (msgKey, msgCmd) = next(((k, v) for k, v in cmds.items() if v.message_id==message_id), (None, None))

    print('here')
    msg = await self.channel.fetch_message(message_id)
    submitter = msg.author.display_name
    createdAt = msg.created_at
    isEdited = msg.edited_at is not None
    approvalReaction = next((r for r in msg.reactions if isinstance(r.emoji, discord.Emoji) and r.emoji.name == 'approved'), None)
    isApproved = approvalReaction is not None #FIXME: reaction isn't found for some reason
    print('here')
    if isApproved:
      if isEdited:
        await self.removeApproval(approvalReaction)
      #TODO: Add "was added" reaction to distinguesh between "approved and pending" and "approved and added"
      if isEdited or msgCmd is not None: #Edits not allowed
        return cmds, False
    elif msgCmd is not None: #Ignore unapproved messages
      return cmds, False #FIXME: Case doesn't work as expected

    print('here')
    #Is unedited and not in the system yet and approved
    attachment = msg.attachments[0] if len(msg.attachments) == 1 else None
    isVideoAttachment = attachment.content_type.split('/')[0] == 'video' if attachment is not None else None
    if not isVideoAttachment:
      return cmds, False
    
    print('here')
    try:
      tomlContent = getCodeBlock(msg.content)
      [(newMsgKey, cmdDict)] = toml.loads(tomlContent).items()
      newMsgCmd = obsVideoCommandsFromDict(cmdDict, dict(sourceName=newMsgKey, path='unspecified'))
      # newMsgCmd.path = None
      newMsgCmd = newMsgCmd._asdict() | dict(path=None)
    except:
      print('here F')
      return cmds, False

    newMsgCmd['submitter'] = submitter
    newMsgCmd['created_at'] = createdAt
    newMsgCmd['message_id'] = message_id
    newMsgCmd['sourceName'] = newMsgKey
    newMsgCmd['path'] = None
    
    print('here A')
    if newMsgKey in cmds: #replace cmd with new command, but only if from same user, or oldcmd not approved anymore
      msgCmd = cmds[newMsgKey]
      sameUser = msgCmd.submitter == newMsgCmd['submitter'] or msgCmd.submitter_twitch == newMsgCmd['submitter_twitch']
      oldmsg = await self.channel.fetch_message(msgCmd.message_id)
      isApproved = next((True for r in oldmsg.reactions if isinstance(r.emoji, discord.Emoji) and r.emoji.name == 'approved'), False)
      if (not sameUser) or isApproved:
        return cmds, False
      newMsgCmd['path'] = msgCmd.path

    print('here')
    if newMsgCmd['path'] is None:
      path0 = self.media_dir / attachment.filename
      parent_path = (path0 / '..').expanduser().resolve()
      validFileName = parent_path.samefile(self.media_dir)
      if not validFileName:
        await self.removeApproval(approvalReaction)
        return cmds, False
      newMsgCmd['path'] = str(path0)
        
    print('here')
    await attachment.save(newMsgCmd['path'])
    cmds[newMsgKey] = ObsVideoCommand(**newMsgCmd)
    return cmds, True


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
  if videoCmdChannel is None:
    videoCmdChannel = await bot.fetch_channel(1047262752604958790)

  msgs = [m async for m in videoCmdChannel.history()]
  # await bot.close()
  return msgs

asyncio.get_event_loop().create_task(runner())
videoCmdChannel = next((ch for ch in bot.get_all_channels() if ch.name=='video-commands' and isinstance(ch, discord.TextChannel)), None)
msgs = asyncio.run(runOnce())

msg0 = msgs[0]
# msg0.content
# print(msg0.id, 'https://discord.com/channels/1039221680054214746/1047262752604958790/1047267620518375425')
# msg0.content
# msg0.reactions
# msg0.created_at
# approvalReaction = next((r for r in msg0.reactions if r.emoji.name == 'approved'), None)
# isApproved = approvalReaction is not None
# msg0.ed

# timestamp = msg0.created_at if msg0.edited_at is None else msg0.edited_at
# media = msg0.attachments[0]
# media.content_type
# asyncio.run(media.save(Path('discord_media/lol.webm')))



videoHnd = videoCommandHandle(msg0.channel, config_file='/home/next/Gits/bot-collection/twitch/BuggyPasta/obs_videos_test.toml')
asyncio.run(videoHnd.handleMessage(msg0.id))



