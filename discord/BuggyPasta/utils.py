from pathlib import Path

def parseStr(s: str, i: int = 0):
  i1 = s.find('"', i)
  if i1 < 0: return None, i1
  i2 = i1+1
  while True:
    i2 = s.find('"', i2)
    if i2 < 0:
      raise ValueError('Unexpected end of string')
    elif s[i2-1] == '\\':
      i2+=1
      continue
    else:
      return s[i1+1 : i2].replace('\\"', '"'), i2+1

class genericEntry:
  def __init__(self, name: str, *args, **kwargs):
    self.name = name
    self.args = list(args)
    self.kwargs = kwargs
  @staticmethod
  def newFrom(raw:str):
    raw = raw.strip()
    if raw == '':
      raise ValueError('Invalid raw-str')
    equalIdx = raw.find('=')
    if equalIdx < 0:
      return genericEntry(raw)
    val = raw[:equalIdx].strip()
    if val == '':
      raise ValueError('Invalid value entry')
    args = raw[equalIdx+1:].strip()
    if args == '':
      raise ValueError('Invalid argument entry')
    elif args[0] == '{' and args[-1] == '}':
      d = {}
      args = args[1:-1]
      while True:
        args = args.strip()
        if args == '': break
        i = args.find('=')
        key = args[:i].strip()
        valI, i = parseStr(args, i)
        if i<0 or val is None: raise ValueError('Invalid raw-str')
        d[key] = valI
        i = args.find(',', i)+1
        args = args[i:] if i>0 else ''
      return genericEntry(val, **d)
    elif args[0] == '[' and args[-1] == ']':
      d = []
      args = args[1:-1]
      while True:
        args = args.strip()
        if args == '': break
        valI, i = parseStr(args)
        if i<0 or val is None: raise ValueError('Invalid raw-str')
        d.append(valI)
        i = args.find(',', i)+1
        args = args[i:] if i>0 else ''
      return genericEntry(val, *d)
    else:
      return genericEntry(val, parseStr(args)[0])
  def __repr__(self) -> str:
    extra = ''
    if self.args:
      extra = f'{self.args if len(self.args)>1 else self.args[0]}'
    if self.kwargs:
      if extra:
        extra += f' + {self.kwargs}'
      else:
        extra = f'{self.kwargs}'
    if extra:
      extra = ' = ' + extra
    return f'Entry[ {self.name}{extra} ]'
  def __str__(self) -> str:
    return repr(self)


class discordEntry:
  def __init__(self, name: str, *args, token=None, **kwargs):
    self.name = name
    self.__token: str|None = token
    self._setToken: bool = token is not None
  def getRunner(self, bot):
    return lambda *args, **kwargs: bot.run(self.__token, *args, **kwargs)
    
  def __repr__(self) -> str:
    return f'DiscordBot[ {self.name}{"" if self._setToken else " (no token set)"} ]'
  def __str__(self) -> str:
    return repr(self)

class config(dict):
  def __init__(self, raw='', **kwargs):
    super().__init__(**kwargs)
    self.__parseRaw(raw)
    self.__parseDiscord()
    self.__parseImport()

  @staticmethod
  def fromFile(path):
    return config(f'[import]\n{path}')

  def getRunner(self, botType: str, botName: str, *args, **kwargs):
    for e in self.get(botType, []):
      if e.name == botName:
        return e.getRunner(*args, **kwargs)
    return None

  def __parseRaw(self, raw: str):
    currentBlock = None
    for l in raw.splitlines():
      l = l.strip()
      if l == '' or l[0] == '#':
        continue
      elif l[0] == '[' and l[-1] == ']':
        currentBlock = l[1:-1]
        self.setdefault(currentBlock, [])
      else:
        self[currentBlock].append(genericEntry.newFrom(l))

  def __parseDiscord(self):
    if 'Discord' not in self:
      return
    self['Discord'] = [discordEntry(e.name, *e.args, **e.kwargs) for e in self['Discord']]

  def __parseImport(self):
    if 'import' not in self:
      return
    imports = self['import']
    del self['import']
    for pEntry in imports:
      path = Path(pEntry.name).expanduser().resolve()
      if not path.exists(): continue
      with open(path, 'r') as f:
        self += config(f.read())

  def __iadd__(self, other: 'config'):
    if not isinstance(other, config):
      return NotImplemented
    for (k, v) in other.items():
      self.setdefault(k, [])
      self[k] += v
    return self
  def __add__(self, other: 'config'):
    if not isinstance(other, config):
      return NotImplemented
    ret = config()
    ret += self
    ret += other
    return ret
    

botConfig = config.fromFile('../../local/config')



