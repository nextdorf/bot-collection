from typing import Any
import nest_asyncio
nest_asyncio.apply() #Wichtig für Jupyter Notebook

try:
  from common.utils import *
except:
  import common
  from utils import *

import asyncio
import websockets.client as wsc
import json
from collections import namedtuple
import hashlib
import base64
from math import inf


OpCode0 = namedtuple('OpCode0', 'obsWSVer rpcVer auth')
OpCode0Auth = namedtuple('OpCode0Auth', 'challenge salt')
OpCode2 = namedtuple('OpCode2', 'rpcVer')
OpCode5 = namedtuple('OpCode5', 'type intent data')
OpCode7 = namedtuple('OpCode7', 'type id status data')
OpCode7Status = namedtuple('OpCode7Status', 'result code comment')

class EventSubscription(int):
  def __and__(self, __n: int) -> 'EventSubscription':
    return EventSubscription(super().__and__(__n))
  def __rand__(self, __n: int) -> 'EventSubscription':
    return self & __n
  def __or__(self, __n: int) -> 'EventSubscription':
    return EventSubscription(super().__or__(__n))
  def __ror__(self, __n: int) -> 'EventSubscription':
    return self | __n
  def __xor__(self, __n: int) -> 'EventSubscription':
    return EventSubscription(super().__xor__(__n))
  def __rxor__(self, __n: int) -> 'EventSubscription':
    return self ^ __n

EventSubscription._None       = EventSubscription(0)
EventSubscription.General     = EventSubscription(1)
EventSubscription.Config      = EventSubscription(1 << 1)
EventSubscription.Scenes      = EventSubscription(1 << 2)
EventSubscription.Inputs      = EventSubscription(1 << 3)
EventSubscription.Transitions = EventSubscription(1 << 4)
EventSubscription.Filters     = EventSubscription(1 << 5)
EventSubscription.Outputs     = EventSubscription(1 << 6)
EventSubscription.SceneItems  = EventSubscription(1 << 7)
EventSubscription.MediaInputs = EventSubscription(1 << 8)
EventSubscription.Vendors     = EventSubscription(1 << 9)
EventSubscription.UI          = EventSubscription(1 << 10)
EventSubscription.AllLower    = EventSubscription((1 << 11) - 1)

EventSubscription.InputVolumeMeters         = EventSubscription(1 << 16)
EventSubscription.InputActiveStateChanged   = EventSubscription(1 << 17)
EventSubscription.InputShowStateChanged     = EventSubscription(1 << 18)
EventSubscription.SceneItemTransformChanged = EventSubscription(1 << 19)



class ObsServer:
  def __init__(self):
    obs:obsEntry = botConfig['Obs']
    self.host = obs._host
    self.port = obs._port
    self.ws: wsc.WebSocketClientProtocol = None
    self.rpcVer = None
  
  async def _connectOnly(self):
    self.ws = await wsc.connect(f'ws://{self.host}:{self.port}')
    return self.ws

  async def _connect(self, pwd: str|None, rpcVer: int|None=None, subscriptions: int|None = None, overrideRpcVer:bool = True):
    if rpcVer is None: rpcVer = self.rpcVer
    if rpcVer is None: rpcVer = inf
    await self._connectOnly()
    helloMsg: OpCode0 = await self.recv()
    idAuth = ObsServer.createAuthentification(helloMsg.auth, pwd)
    await self.sendIdentify(min(helloMsg.rpcVer, rpcVer), idAuth, subscriptions)
    helloMsg2: OpCode2 = await obs.recv()
    if overrideRpcVer:
      self.rpcVer = helloMsg2.rpcVer
    return helloMsg2.rpcVer


  async def recv(self):
    msg: dict[str, any] = json.loads(await self.ws.recv())
    op: int = msg['op']
    d: dict = msg['d']
    if op == 0:
      obsWSVer, rpcVer, auth = [d.get(k, None) for k in 'obsWebSocketVersion rpcVersion authentication'.split()]
      if auth:
        auth = OpCode0Auth(**auth)
      return OpCode0(obsWSVer, rpcVer, auth)
    elif op == 2:
      return OpCode2(d['negotiatedRpcVersion'])
    elif op == 5:
      return OpCode5(d['eventType'], d['eventIntent'], d['eventData'])
    elif op == 7:
      status: dict
      type, id, status, data = [d.get(k, None) for k in 'requestType requestId requestStatus responseData'.split()]
      status.setdefault('comment', None)
      status = OpCode7Status(**status)
      return OpCode7(type, id, status, data)
    else:
      return msg

  async def sendArgs(self, sep='_', **kwargs):
    msg = {}
    kStr: str
    for kStr,v in kwargs.items():
      if v is None: continue
      ks = kStr.split(sep)
      d = msg
      for k in ks[:-1]:
        d.setdefault(k, {})
        d = d[k]
      d[ks[-1]] = v
    msgStr = json.dumps(msg)
    return await self.ws.send(msgStr)

  async def sendIdentify(self, rpcVer: int, idAuth:str|None, subscribtions:int|None = None):
    await self.sendArgs(op=1,
      d_rpcVersion=rpcVer, d_authentication=idAuth, d_eventSubscriptions=subscribtions)

  async def sendReidentify(self, subscriptions:int|None = None):
    await self.sendArgs(op=3, d_eventSubscriptions=subscriptions)

  async def sendRquest(self, type:str, id:str, data:None|Any = None, sep='_', **innerData):
    kwargs = {}
    kwargs[f'd{sep}requestType'] = type
    kwargs[f'd{sep}requestId'] = id
    kwargs[f'd{sep}requestData'] = data
    for k,v in innerData.items():
      kwargs[sep.join(['d', 'requestData', k])] = v
    await self.sendArgs(op=6, sep=sep, **kwargs)

  @staticmethod
  def createAuthentification(helloAuth: OpCode0Auth|None, pwd: str):
    def sha256AndBase64(s:str):
      sha256 = hashlib.sha256(s.encode('ascii')).digest()
      b64 = base64.b64encode(sha256)
      return b64.decode('ascii')
    if helloAuth is None or pwd is None: return None
    salted:str = pwd + helloAuth.salt
    base64_secret = sha256AndBase64(salted)
    auth = sha256AndBase64(base64_secret + helloAuth.challenge)
    return auth

  @staticmethod
  def minVersion(*vs: str):
    ws = [list(map(int, v.split('.'))) for v in vs]
    n = max(map(len, ws))
    for i in range(len(ws)):
      m = n - len(ws[i])
      if m > 0:
        ws[i] = [0]*m + ws[i]
    return '.'.join(map(str, min(ws)))

obs = ObsServer()
asyncio.run(botConfig['Obs'].apply(obs)(subscriptions=0))


#asyncio.run(obs.sendRquest('GetSceneItemList', 'AAA', sceneName='Scene 3'))
asyncio.run(obs.sendRquest('GetInputList', ''))
inputList = asyncio.run(obs.recv())
inputList

inputName = 'Image'
asyncio.run(obs.sendRquest('GetInputSettings', '', inputName=inputName))
img = asyncio.run(obs.recv())
img

overrideInputSettings = dict(file='path/to/image')
asyncio.run(obs.sendRquest('SetInputSettings', '', inputName=inputName, inputSettings=overrideInputSettings))
res = asyncio.run(obs.recv())
res

