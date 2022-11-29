from pathlib import Path
from typing import Callable
import toml
import string
import secrets
import asyncio
import http
import http.server
import urllib.parse
import os


class discordEntry:
  def __init__(self, name: str, *args, token=None, **kwargs):
    self.name = name
    self.__token: str|None = token
    self._setToken: bool = token is not None
  def apply(self, bot, run_async=False):
    if run_async:
      return lambda *args, **kwargs: bot.start(self.__token, *args, **kwargs)
    else:
      return lambda *args, **kwargs: bot.run(self.__token, *args, **kwargs)
    
  def __repr__(self) -> str:
    return f'DiscordBot[ {self.name}{"" if self._setToken else " (no token set)"} ]'
  def __str__(self) -> str:
    return repr(self)


class AccessTokenHandle(http.server.BaseHTTPRequestHandler):
  access_token = None
  logging = True
  def do_GET(self):
    host, _ = self.client_address
    _, port = self.server.server_address
    html = f'''
      <!DOCTYPE html>
      <html>
      <head></head>
      <body>
        <script>
          window.onload = function() {{
            document.getElementById('text').innerHTML = "Loading...";
            if(document.location.hash.length > 0) {{
              var newUri = 'http://{host}:{port}/?' + document.location.hash.slice(1);
              var inner = '<a href="'+newUri+'"> <span class="link">'+newUri+'</span> </a>';
              document.getElementById('text').innerHTML = inner;
              document.location = newUri;
            }}
            else {{
              document.getElementById('text').innerHTML = 'SUCCESS! You can close this page now.';
              window.close();
            }}
          }};
        </script>

        <div id="text" class="container">Automation requires Javascript...</div>
      </body>
      </html>'''.encode('ascii')
    self.send_response(http.HTTPStatus.OK)
    self.send_header('Content-type', 'text/html')
    self.send_header('Content-Length', str(len(html)))
    self.end_headers()
    self.wfile.write(html)
    req = self.requestline
    access_id = 'access_token='
    i1 = req.find(access_id)
    i2 = req.find('&', i1)
    if i1 < 0 or i2 < 0:
      self.log_message('GET: RETRY')
    else:
      i1 += len(access_id)
      parsed = req[i1 : i2]
      AccessTokenHandle.access_token = parsed
      self.log_message('GET: ' + parsed)
      AccessTokenHandle.logging = False
  def log_message(self, format: str, *args):
    if AccessTokenHandle.logging:
      super().log_message(format, *args)

class twitchEntry:
  def __init__(self, name: str, *args, client_id=None, secret=None, redirect_uri=None, scope=[], force_verify=True, set_state=True, **kwargs):
    self.name = name
    self._client_id: str|None = client_id
    self.__secret: str|None = secret
    self._force_verify: bool|None = force_verify
    self._redirect_uri: str|None = redirect_uri
    self._scope: list[str] = scope
    self._set_state: bool = set_state
    self._valid: bool = all([x is not None for x in [client_id, redirect_uri, scope]])

  @property
  def randomState(self):
    return ''.join([secrets.choice(string.ascii_letters + string.digits) for _ in range(16)])

  @property
  def accessTokenLink(self):
    if not self._valid:
      return None
    state = self.randomState if self._set_state else None
    ret = ('https://id.twitch.tv/oauth2/authorize'
      + '?response_type=token'
      + f'&client_id={self._client_id}'
      + f'&redirect_uri={self._redirect_uri}'
      + (f'&force_verify={"true" if self._force_verify else "false"}' if self._force_verify else '')
      + f'&scope={"+".join(self._scope)}'.replace(':', '%3A')
      + (f'&state={state}' if state is not None else '')
      )
    return ret

  async def generateAccessToken(self, username, httpTimeout=180, openUrlCmd='xdg-open "%s"'):
    accessLink = self.accessTokenLink
    print(f'* Generate access token for {username}:\n  Open "{accessLink}" in your browser (server timesout in {httpTimeout}s)')
    url0 = self._redirect_uri
    if url0.find('://') < 0: url0 = 'http://'+url0
    url = urllib.parse.urlparse(url0)
    if url.netloc.find(':') < 0: url.netloc += ':80'
    host, portStr = url.netloc.split(':')
    port = int(portStr)

    with http.server.HTTPServer(('localhost', port), AccessTokenHandle) as httpd:
      AccessTokenHandle.access_token = None
      AccessTokenHandle.logging = False
      httpd.timeout = httpTimeout
      def fnTimeout():
        AccessTokenHandle.access_token = 'TIMEOUT'
      httpd.handle_timeout = fnTimeout

      try:
        if openUrlCmd:
          os.system(openUrlCmd % accessLink)
      except:
        pass
      while AccessTokenHandle.access_token is None:
        httpd.handle_request()
    
    if AccessTokenHandle.access_token in [None, 'TIMEOUT', '']:
      return None
    else:
      return AccessTokenHandle.access_token


  def apply(self, bot):
    return lambda *args, **kwargs: bot.run(self.__token, *args, **kwargs)
    
  def __repr__(self) -> str:
    scope = ', scope = [%s]' % (', '.join(self._scope))
    return f'TwitchBot[ {self.name}{scope if self._valid else " (not all fields are set)"} ]'
  def __str__(self) -> str:
    return repr(self)

class twitchUserEntry:
  def __init__(self, name: str, twitchApp: twitchEntry, *args, access_token:str|None=None, **kwargs):
    self.name = name
    self.twitchApp = twitchApp
    self.__access_token: str|None = None
    self._access_token_kind: str|bool = False
    self._valid: bool = bool(access_token)

    if self._valid:
      token_lower = access_token.lower()
      if token_lower.startswith('auto_') and token_lower.endswith('_'):
        self._access_token_kind = access_token
      else:
        self._access_token_kind = True
        self.__access_token = access_token

  async def generateAccessToken(self, files:list[str], **kwargs):
    if isinstance(self._access_token_kind, str):
      accessToken:str|None = await self.twitchApp.generateAccessToken(self.name, **kwargs)
      if accessToken:
        for path in files:
          file = str(Path(path).expanduser().resolve())
          content = None
          with open(file, 'r') as f:
            content = f.read()
          if content.find(self._access_token_kind) < 0:
            continue
          content = content.replace(self._access_token_kind, accessToken)
          with open(file, 'w') as f:
            f.write(content)
        self.__access_token = accessToken
        self._access_token_kind = True
      else:
        self.__access_token = None
        self._access_token_kind = False
    self._valid = bool(self.__access_token)
    return self._valid

  def apply(self, setTokenFn: Callable[[str], any]):
    return setTokenFn(self.__access_token)
    
  def __repr__(self) -> str:
    return f'TwitchBot[ {self.name}{"" if self._valid else " (not all fields are set)"} | {self.twitchApp.name} ]'
  def __str__(self) -> str:
    return repr(self)


class obsEntry:
  def __init__(self, name: str, *args, host='localhost', port=4455, password:str|None=None, **kwargs):
    self.name = name
    self._host = host
    self._port = port
    self.__password = password
  def apply(self, obs: 'ObsClient'):
    return lambda **kwargs: obs._connect(pwd=self.__password, **kwargs)

  def __repr__(self) -> str:
    return f'Obs[ {self.name}@{self._host} ]'
  def __str__(self) -> str:
    return repr(self)


def appendCollection(a: list|dict, b: list|dict):
  if isinstance(a, dict):
    if isinstance(b, dict):
      for k, v in b.items():
        if k in a:
          appendCollection(a[k], b[k])
        else:
          a[k] = v
    elif b is None:
      return
    else:
      raise ValueError()
  elif isinstance(a, list):
    if isinstance(b, list):
      for bi in b:
        a.append(bi)
    elif b is not None:
      a.append(b)
    else:
      raise ValueError()
  else:
    raise ValueError()

class config(dict):
  def __init__(self, raw='', source = None, **kwargs):
    args = toml.loads(raw)
    for k, v in kwargs.items():
      args[k] = v
    super().__init__(**args)
    self.source = source
    self.refPaths: list[Path] = []
    self.__parseDiscord()
    self.__parseTwitch()
    self.__parseObs()
    self.__parseImport()

  @staticmethod
  def fromFile(path):
    return config(f'import = "{path}"')

  def apply(self, botType: str, botName: str, *args, **kwargs):
    unnestedBotNames = botName.split('.')
    for entry in self.get(botType, []):
      cont = False
      innerEntry = entry
      for e in unnestedBotNames[:-1]:
        if not isinstance(innerEntry, dict):
          cont = True
          break
        else:
          innerEntry = innerEntry[e]
      if cont: continue
      if innerEntry.name == unnestedBotNames[-1]:
        return innerEntry.apply(*args, **kwargs)
    return None

  def __parseDiscord(self):
    if 'Discord' not in self:
      return
    self['Discord'] = { name: discordEntry(name, **vals) for name, vals in self['Discord'].items() }

  def __parseTwitch(self):
    if 'Twitch' not in self:
      return
    tmp = {}
    for name, vals in self['Twitch'].items():
      tmp[name] = {}
      app = twitchEntry(name, **vals)
      tmp[name]['App'] = app
      tokens: dict[str, str] = vals.get('access_tokens', {})
      for user, token in tokens.items():
        tmp[name][user] = twitchUserEntry(user, app, access_token=token)
    self['Twitch'] = tmp

  def __parseObs(self):
    if 'Obs' not in self:
      return
    self['Obs'] = obsEntry('Obs-websocket', **self['Obs'])

  def __parseImport(self):
    if 'import' not in self:
      return
    importPath = Path(self['import']).expanduser().resolve()
    del self['import']
    if importPath.exists():
      self.refPaths.append(importPath)
      content = ''
      with open(str(importPath), 'r') as f:
        content = f.read()
      self += config(content, str(importPath))

  async def generateTwitchAccessTokens(self):
    ret = {}
    files = list(map(str, self.refPaths))
    name: str
    for name, users in self['Twitch'].items():
      app: twitchEntry = users['App']
      user: str
      bot: twitchUserEntry
      for user, bot in users.items():
        if user == 'App': continue
        hasAccess = await bot.generateAccessToken(files)
        ret['.'.join([name, user])] = hasAccess
    return ret



  def __iadd__(self, other: 'config'):
    if not isinstance(other, config):
      return NotImplemented
    appendCollection(self, other)
    self.refPaths += other.refPaths
    return self
  def __add__(self, other: 'config'):
    if not isinstance(other, config):
      return NotImplemented
    ret = config()
    ret += self
    ret += other
    return ret

  def __repr__(self) -> str:
    tomlRepr = toml.dumps(self)
    header = f'# Source: {self.source}\n'
    for p in self.refPaths:
      header += f'# {p}\n'
    return f'{header}\n{tomlRepr}'
  def __str__(self) -> str:
    return repr(self)
    

# botConfig = config.fromFile('../local/config')
botConfig = config.fromFile('~/.config/bot-collection/config')
if __name__ == '__main__':
  botConfig
  w = asyncio.run(botConfig.generateTwitchAccessTokens())
  print(w)

