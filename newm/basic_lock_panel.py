import websockets
import json
import getpass
import asyncio

from .panel_endpoint import SOCKET_PORT

def basic_lock_panel():
    async def _send():
        uri = "ws://127.0.0.1:%d" % SOCKET_PORT
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps({ 'kind': 'auth_register' }))

            while True:
                response = json.loads(await websocket.recv())
                if response['kind'] == 'auth_request_cred':
                    print(response['message'])
                    cred = getpass.getpass()

                    await websocket.send(json.dumps({ 'kind': 'auth_enter_cred', 'cred': cred}))

    asyncio.get_event_loop().run_until_complete(_send())
