try:
  from common.utils import *
except:
  import common
  from utils import *

import discord
from discord.ext.commands import Bot, Context, Cog
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

def isApprovalEmoji(emoji: discord.PartialEmoji | discord.Emoji | str):
  if isinstance(emoji, discord.PartialEmoji) or isinstance(emoji, discord.Emoji):
    return emoji.name.lower() == 'approved'
  else:
    return False


class videoCommandHandle(Cog):
  def __init__(self, bot:Bot, media_dir:Path|str='discord_media', config_file:Path|str='obs_videos.toml'):
    self._bot = bot
    self.channel: discord.TextChannel = None
    if not isinstance(media_dir, Path): media_dir = Path(media_dir)
    if not media_dir.is_dir(): media_dir = None
    self.media_dir = media_dir
    if not isinstance(config_file, Path): config_file = Path(config_file)
    if not config_file.is_file() : config_file = None
    self.config_file = config_file
    super().__init__()

  async def cog_load(self):
    print('Loading videoCommandHandle...')
    #if ch.name.lower()=='video-commands':
    self.channel = await bot.fetch_channel(1047262752604958790)
    await self.handleHistory()

  async def removeApproval(self, approvalReaction: discord.Reaction):
    if approvalReaction is None:
      return
    async for user in approvalReaction.users():
      await approvalReaction.remove(user)

  async def handleMessage(self, message_id: int|discord.Message, cmds: dict[str, 'ObsVideoCommand']|None=None):
    if cmds is None:
      with open(str(self.config_file), 'r') as f:
        cmds = obsVideoCommandsFromToml(f.read())
    (msgKey, msgCmd) = next(((k, v) for k, v in cmds.items() if v.message_id==message_id), (None, None))

    if isinstance(message_id, discord.Message):
      msg = message_id
      message_id = msg.id
    else:
      msg = await self.channel.fetch_message(message_id)
    submitter = msg.author.display_name
    createdAt = msg.created_at
    isEdited = msg.edited_at is not None
    approvalReaction = next((r for r in msg.reactions if isApprovalEmoji(r.emoji)), None)
    isApproved = approvalReaction is not None
    if isApproved:
      if isEdited:
        await self.removeApproval(approvalReaction)
      #TODO: Add "was added" reaction to distinguesh between "approved and pending" and "approved and added"
      if isEdited or msgCmd is not None: #Edits not allowed
        return cmds, None
    else:
      return cmds, None

    #Is unedited and not in the system yet and approved
    attachment = msg.attachments[0] if len(msg.attachments) == 1 else None
    isVideoAttachment = attachment.content_type.split('/')[0] == 'video' if attachment is not None else None
    if not isVideoAttachment:
      return cmds, None
    
    try:
      tomlContent = getCodeBlock(msg.content)
      [(newMsgKey, cmdDict)] = toml.loads(tomlContent).items()
      newMsgCmd = obsVideoCommandsFromDict(cmdDict, dict(sourceName=newMsgKey, path='unspecified'))
      # newMsgCmd.path = None
      newMsgCmd = newMsgCmd._asdict() | dict(path=None)
    except:
      return cmds, None

    newMsgCmd['submitter'] = submitter
    newMsgCmd['created_at'] = createdAt
    newMsgCmd['message_id'] = message_id
    newMsgCmd['sourceName'] = newMsgKey
    newMsgCmd['path'] = None
    
    if newMsgKey in cmds: #replace cmd with new command, but only if from same user, or oldcmd not approved anymore
      msgCmd = cmds[newMsgKey]
      sameUser = msgCmd.submitter == newMsgCmd['submitter'] or msgCmd.submitter_twitch == newMsgCmd['submitter_twitch']
      if msgCmd.message_id is not None:
        oldmsg = await self.channel.fetch_message(msgCmd.message_id)
        isApproved = next((True for r in oldmsg.reactions if isApprovalEmoji(r.emoji)), False)
      else:
        isApproved = True
      if (not sameUser) or isApproved:
        return cmds, None
      newMsgCmd['path'] = msgCmd.path

    if newMsgCmd['path'] is None:
      path0 = self.media_dir / attachment.filename
      parent_path = (path0 / '..').expanduser().resolve()
      validFileName = parent_path.samefile(self.media_dir)
      if not validFileName:
        await self.removeApproval(approvalReaction)
        return cmds, None
      newMsgCmd['path'] = str(path0)
        
    await attachment.save(newMsgCmd['path'])
    cmds[newMsgKey] = ObsVideoCommand(**newMsgCmd)
    return cmds, newMsgKey

  async def handleHistory(self):
    cmds = None
    newCmds = []
    async for msg in self.channel.history():
      cmds, newCmd = await self.handleMessage(msg, cmds)
      if newCmd is not None:
        newCmds.append(newCmd)
    if newCmds and cmds is not None:
      print('New Commands added:', ', '.join(newCmds))
      tomlContent = obsVideoCommandsIntoToml(cmds)
      with open(self.config_file, 'w+') as f:
        f.write(tomlContent)

  async def handleSingleMessage(self, msg:discord.Message|int):
    cmds, newCmd = await self.handleMessage(msg)
    if newCmd is not None and cmds is not None:
      print('New Command added:', newCmd)
      tomlContent = obsVideoCommandsIntoToml(cmds)
      with open(self.config_file, 'w+') as f:
        f.write(tomlContent)

  @discord.ext.commands.command()
  async def ping(self, ctx: Context):
    await ctx.send('pong (Twitchbot)')

  @Cog.listener()
  async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
    msg_id = payload.message_id
    emoji = payload.emoji
    if payload.user_id == bot.user.id:
      return
    print(f'User #{payload.user_id} reacted with {emoji.name}')
    await videoHnd.handleSingleMessage(msg_id)

intents = discord.Intents.default()

intents.message_content = True
intents.reactions = True
intents.members = True
bot = Bot(command_prefix='!', intents=intents)

videoHnd = videoCommandHandle(bot, config_file='obs_videos_test.toml')


runner = botConfig['Discord']['BuggyPasta'].apply(bot, run_async=True)

asyncio.get_event_loop().create_task(runner())

asyncio.run(bot.add_cog(videoHnd))

bot.extra_events





