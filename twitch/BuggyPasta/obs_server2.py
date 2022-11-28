from typing import Any, Awaitable
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
from pathlib import Path
import PIL.Image
import random

OpCode0 = namedtuple('OpCode0', 'obsWSVer rpcVer auth')
OpCode0Auth = namedtuple('OpCode0Auth', 'challenge salt')
OpCode2 = namedtuple('OpCode2', 'rpcVer')
OpCode5 = namedtuple('OpCode5', 'type intent data')
OpCode7 = namedtuple('OpCode7', 'type id status data')
OpCode7Status = namedtuple('OpCode7Status', 'result code comment')

class EventSubscription(int):
  _None: 'EventSubscription' = None
  General: 'EventSubscription' = None
  Config: 'EventSubscription' = None
  Scenes: 'EventSubscription' = None
  Inputs: 'EventSubscription' = None
  Transitions: 'EventSubscription' = None
  Filters: 'EventSubscription' = None
  Outputs: 'EventSubscription' = None
  SceneItems: 'EventSubscription' = None
  MediaInputs: 'EventSubscription' = None
  Vendors: 'EventSubscription' = None
  UI: 'EventSubscription' = None
  AllLower: 'EventSubscription' = None
  InputVolumeMeters: 'EventSubscription' = None
  InputActiveStateChanged: 'EventSubscription' = None
  InputShowStateChanged: 'EventSubscription' = None
  SceneItemTransformChanged: 'EventSubscription' = None

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


class EventListener:
  def __init__(self, func: Callable[['EventListener', OpCode5], Awaitable[bool]], **kwargs):
    self.func = func
    for (k, v) in kwargs.items():
      setattr(self, k, v)
  async def __call__(self, event: OpCode5) -> bool:
    'Returns whether listener wants to continue to listen to future events'
    return await self.func(self, event)


class ObsServer:
  def __init__(self):
    obs:obsEntry = botConfig['Obs']
    self.host = obs._host
    self.port = obs._port
    self.ws: wsc.WebSocketClientProtocol = None
    self.rpcVer = None
    self.eventListeners = []
  
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
    helloMsg2: OpCode2 = await self.recv()
    if overrideRpcVer:
      self.rpcVer = helloMsg2.rpcVer
    return helloMsg2.rpcVer

  async def handleListeners(self, event: OpCode5):
    i = 0
    while i < len(self.eventListeners):
      listener = self.eventListeners[i]
      continueListening = await listener(event)
      if not continueListening:
        del self.eventListeners[i]
      else:
        i+=1



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
      event = OpCode5(d['eventType'], d['eventIntent'], d['eventData'])
      await self.handleListeners(event)
      return event
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

  async def sendRequest(self, type:str, id:str, data:None|Any = None, sep='_', **innerData):
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

  async def getResponse(self, type:str, id:str, data:None|Any = None, sep='_', **innerData):
    await self.sendRequest(type, id, data, sep, **innerData)
    ret: OpCode7|None = None
    while not (isinstance(ret, OpCode7) and ret.id == id):
      ret = await self.recv()
    return ret

  async def noImage(self, sceneName:str, itemName: str):
    idStr = f'noItem({sceneName}, {itemName})'
    fullId = f'{idStr}_{random.randint(0, 999)}'

    overrideInputSettings = dict(file='')
    resp = await self.getResponse('SetInputSettings', fullId,
      inputName=itemName, inputSettings=overrideInputSettings)
    status: OpCode7Status = resp.status
    return status

  async def changeImage(self, sceneName:str, itemName: str, path: str|None, width: int, height:int, srcWidth: int|None=None, srcHeight: int|None=None):
    if path is None:
      return await self.noImage(sceneName, itemName)
    if width is None and height is None:
      return
    absPath = (Path('.') / path).expanduser().resolve()
    if not (absPath.exists() and absPath.is_file()):
      return None
    absPath = str(absPath)
    if srcWidth is None or srcHeight is None:
      img = PIL.Image.open(absPath)
      srcWidth, srcHeight = img.size

    idStr = f'changeItem({sceneName}, {itemName}, {path}, {width}, {height})'
    fullId = f'{idStr}_{random.randint(0, 999)}'

    overrideInputSettings = dict(file=absPath)
    resp = await self.getResponse('SetInputSettings', fullId,
      inputName=itemName, inputSettings=overrideInputSettings)
    status: OpCode7Status = resp.status
    if not status.result:
      return status

    sceneItems = await self.getResponse('GetSceneItemList', fullId,
      sceneName='Screen')
    status: OpCode7Status = sceneItems.status
    if not status.result:
      return status

    possibleItems = [x for x in sceneItems.data['sceneItems'] if x['sourceName'] == itemName]
    imgItem = possibleItems[0]
    newTransformation:dict = imgItem['sceneItemTransform'].copy()
    newTransformation.update(dict(
      scaleX=width/srcWidth if width is not None else height/srcHeight,
      scaleY=height/srcHeight if height is not None else width/srcWidth
      ))
    resp = await self.getResponse('SetSceneItemTransform', fullId, 
      sceneName=sceneName,
      sceneItemId=imgItem['sceneItemId'],
      sceneItemTransform = newTransformation
      )
    status: OpCode7Status = resp.status
    return status

  async def restartVideo(self, sceneName:str, itemName: str):
    print(itemName)
    idStr = f'restartVideo({sceneName}, {itemName})'
    fullId = f'{idStr}_{random.randint(0, 999)}'
    resp = await self.getResponse('TriggerMediaInputAction', fullId, 
      inputName=itemName,
      mediaAction = 'OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART' )
    print(resp)
    status: OpCode7Status = resp.status
    return status


  async def startVideo(self, name: str, volume_in_db:int, path: str|Path, transformation:dict[str, str], monitor_type='OBS_MONITORING_TYPE_MONITOR_ONLY', sceneName='Screen'):
    if not isinstance(path, Path): path = Path(path)
    path = str(path.expanduser().resolve())
    idStr = f'startVideo({name}, {volume_in_db}, {path})'
    fullId = f'{idStr}_{random.randint(0, 999)}'
    status: OpCode7Status

    resp = await self.getResponse('CreateInput', fullId, 
      sceneName = sceneName, inputName=name, inputKind='ffmpeg_source')
    status = resp.status
    if not status.result:
      return status
    sceneItemId = resp.data['sceneItemId']

    resp = await self.getResponse('SetInputAudioMonitorType', fullId,
      inputName=name, monitorType=monitor_type)
    status = resp.status
    if not status.result:
      await self.getResponse('RemoveSceneItem', fullId, sceneName=sceneName, sceneItemId=sceneItemId)
      return status

    resp = await self.getResponse('SetSceneItemTransform', fullId,
      sceneName=sceneName, sceneItemId=sceneItemId, sceneItemTransform=sceneItemTransform)
    status = resp.status
    if not status.result:
      await self.getResponse('RemoveSceneItem', fullId, sceneName=sceneName, sceneItemId=sceneItemId)
      return status
    
    resp = await self.getResponse('SetInputVolume', fullId,
      inputName=name, inputVolumeDb=volume_in_db)
    status = resp.status
    if not status.result:
      await self.getResponse('RemoveSceneItem', fullId, sceneName=sceneName, sceneItemId=sceneItemId)
      return status

    resp = await self.getResponse('CreateSourceFilter', fullId,
      sourceName=name, filterName='Chroma Key', filterKind='chroma_key_filter_v2',
      filterSettings=dict(key_color_type='green'))
    status = resp.status
    if not status.result:
      await self.getResponse('RemoveSceneItem', fullId, sceneName=sceneName, sceneItemId=sceneItemId)
      return status

    resp = await self.getResponse('SetInputSettings', fullId,
      inputName=name, inputSettings=dict(local_file=path))
    status = resp.status
    if not status.result:
      await self.getResponse('RemoveSceneItem', fullId, sceneName=sceneName, sceneItemId=sceneItemId)
      return status

    async def callback(listener: EventListener, event: OpCode5):
      if not (
              event.intent|EventSubscription.MediaInputs
          and event.type == 'MediaInputPlaybackEnded'
          and event.data.get('inputName') == listener.inputName
          ):
        return True
      else:
        await self.getResponse('RemoveSceneItem', fullId, sceneName=sceneName, sceneItemId=sceneItemId)
        return False

    listener = EventListener(callback, inputName=name)
    self.eventListeners.append(listener)
    return status


if __name__ == '__main__':
  obs = ObsServer()
  restartAction = 'OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART'
  asyncio.run(botConfig['Obs'].apply(obs)(subscriptions=EventSubscription.MediaInputs))
  resp = asyncio.run(obs.getResponse('GetSceneItemList', '', 
    sceneName='Videos'))
  resp

  
  inputName = 'new_video'
  volume_in_db = -12
  test_path = Path('videos/lol.webm')
  monitor_type = 'OBS_MONITORING_TYPE_MONITOR_ONLY'
  sceneItemTransform = dict(
    alignment = 5,
    cropBottom = 0,
    cropLeft = 320,
    cropRight = 300,
    cropTop = 0,
    height = 0.0,
    positionX = 728.5416259765625,
    positionY = 285.0,
    rotation = 0.0,
    scaleX = -0.5604166388511658,
    scaleY = 0.5601851940155029,
    sourceHeight = 0.0,
    sourceWidth = 0.0,
    width = -0.0
  )

  resp = asyncio.run(obs.startVideo(inputName, volume_in_db, test_path, sceneItemTransform))
  resp
  while True:
    asyncio.run(obs.recv())

  # resp = asyncio.run(obs.getResponse('CreateInput', '', 
  #   sceneName = 'Screen', inputName=inputName, inputKind='ffmpeg_source'))
  # resp
  # sceneItemId = resp.data['sceneItemId']

  # resp = asyncio.run(obs.getResponse('SetInputAudioMonitorType', '',
  #   inputName=inputName, monitorType=monitor_type))
  # resp

  # resp = asyncio.run(obs.getResponse('SetSceneItemTransform', '',
  #   sceneName='Screen', sceneItemId=sceneItemId, sceneItemTransform=sceneItemTransform))
  # resp
  
  # resp = asyncio.run(obs.getResponse('SetInputVolume', '',
  #   inputName=inputName, inputVolumeDb=volume_in_db))
  # resp

  # resp = asyncio.run(obs.getResponse('CreateSourceFilter', '',
  #   sourceName=inputName, filterName='Chroma Key', filterKind='chroma_key_filter_v2',
  #   filterSettings=dict(key_color_type='green')))
  # resp

  # resp = asyncio.run(obs.getResponse('SetInputSettings', '',
  #   inputName=inputName, inputSettings=dict(local_file=test_path)))
  # resp

  # resp0: None|OpCode5 = None
  # while not (isinstance(resp0, OpCode5) and resp0.intent|EventSubscription.MediaInputs and resp0.type == 'MediaInputPlaybackEnded'):
  #   resp0 = asyncio.run(obs.recv())

  # resp = asyncio.run(obs.getResponse('RemoveSceneItem', '', 
  #   sceneName='Screen', sceneItemId=sceneItemId))
  # resp


  # resp = asyncio.run(obs.getResponse('TriggerMediaInputAction', '', 
  #   inputName='rusure', mediaAction = restartAction))
  # resp

  # status = asyncio.run(obs.changeImage('Screen', 'Image', 'images/Tux.png', 300, 300))
  # status = asyncio.run(obs.changeImage('Screen', 'Image', None, 300, 300))



