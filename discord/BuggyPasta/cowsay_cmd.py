from discord.ext.commands import Bot, Command, Context, command
import subprocess


def runUnixCmd(*args):
  res = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8', env={})
  return res.stdout


class Cowsay:
  def __init__(self):
    # runUnixCmd(*'cowsay 💕💕💕 ඞ'.split())
    self.brief = runUnixCmd(*'cowsay -h'.split()).replace('cowsay', '%s')
    self.charList = '\n'.join(runUnixCmd(*'cowsay -l'.split()).split('\n')[1:]).split()

  async def cowcom(self, ctx: Context, *args: str, cowcommand='cowsay'):
    if cowcommand not in 'cowsay cowthink'.split():
      return
    param0s = 'bdgpstwyhl'
    param1s = 'efTW'
    foundParams = {}
    i, l = 0, len(args)
    while i<l:
      a = args[i]
      if a.startswith('-'):
        p0s = ''.join([si for si in a[1:] if si in param0s])
        p1s = ''.join([si for si in a[1:] if si in param1s])
        if p0s:
          if p1s:
            return
          else:
            for si in p0s: foundParams[si] = ()
            i += 1
        elif len(p1s) == 1:
          foundParams[p1s] = args[i+1]
          i += 2
        else:
          return
      else:
        foundParams['args'] = ' '.join(args[i:])
        break

    if 'f' in foundParams:
      foundParams['f'] = foundParams['f'].lower()
      if foundParams['f'] not in self.charList:
        return

    foundParams.setdefault('args', ' ')
    if 'l' in foundParams:
      await ctx.send(f'Alternative cows you can select in combination with `-f`:\n```{", ".join(self.charList)}```')
    elif 'h' in foundParams:
      await ctx.send(f'```{self.brief}```' % cowcommand)
    else:
      unixArgs = [cowcommand]
      p0s = [p for p in param0s if p in foundParams]
      if p0s:
        unixArgs.append('-' + ''.join(p0s))
      p1s = [p for p in param1s if p in foundParams]
      for p in p1s:
        unixArgs += ['-'+p, foundParams[p]]
      unixArgs.append(foundParams['args'])
      await ctx.send(f'```{runUnixCmd(*unixArgs)}```')

  def addCommandsToBot(self, bot: Bot):
    for cmd in 'cowsay cowthink'.split():
      bot.add_command(command(
        name=cmd,
        brief=self.brief % cmd
      )(getattr(self, cmd)))


