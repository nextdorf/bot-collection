import nest_asyncio
nest_asyncio.apply() #Wichtig für Jupyter Notebook

import asyncio
import websockets.client as wsc

host = 'localhost'


ws:wsc.WebSocketClientProtocol = asyncio.run(wsc.connect(f'ws://{host}:{port}'), debug=True)


asyncio.run(ws.recv())

