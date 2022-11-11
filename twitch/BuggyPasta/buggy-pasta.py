try:
  from common.utils import *
except:
  import common
  from utils import *

from twitchio.ext import commands

buggyPastaConfig = botConfig['Twitch']['BuggyPasta']

class Bot(commands.Bot):
  def __init__(self, botUser: str, channels=[]):
    # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
    # prefix can be a callable, which returns a list of strings or a string...
    # initial_channels can also be a callable which returns a list of strings...
    self.botUserConfig: twitchUserEntry = buggyPastaConfig[botUser]
    self.botUserConfig.apply(
      lambda token: super(Bot, self).__init__(token=token, prefix='?', initial_channels=channels)
      )

  async def event_ready(self):
    # Notify us when everything is ready!
    # We are logged in and ready to chat and use commands...
    print(f'Logged in as | {self.nick}')
    print(f'User id is | {self.user_id}')

  @commands.command()
  async def hello(self, ctx: commands.Context):
    # Here we have a command hello, we can invoke our command with our prefix and command name
    # e.g ?hello
    # We can also give our commands aliases (different names) to invoke with.

    # Send a hello back!
    # Sending a reply back to the channel is easy... Below is an example.
    await ctx.send(f'Hello {ctx.author.name}!')


bot = Bot('buggynoodles', ['NextBigIdea'])
bot.run()
# bot.run() is blocking and will stop execution of any below code here until stopped or closed.






