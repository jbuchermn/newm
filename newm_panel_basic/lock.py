import websockets
import json
import getpass
import asyncio
import os
import time

from newm import SOCKET_PORT

def run():
    async def _run():
        uri = "ws://127.0.0.1:%d" % SOCKET_PORT
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps({ 'kind': 'auth_register' }))

            while True:
                response = json.loads(await websocket.recv())
                if response['kind'] == 'auth_request_cred':
                    os.system("clear")
                    print("")
                    print("")
                    print("")
                    cred = getpass.getpass(prompt=response['message'])

                    await websocket.send(json.dumps({ 'kind': 'auth_enter_cred', 'cred': cred}))
                elif response['kind'] == 'auth_request_user':
                    os.system("clear")
                    print("")
                    print("")
                    print("")
                    user = input("Pick a user - %s: " % " /".join(response['users']))

                    await websocket.send(json.dumps({ 'kind': 'auth_choose_user', 'user': user}))
                else:
                    break

    asyncio.get_event_loop().run_until_complete(_run())

def lock():
    while True:
        try:
            run()
        except Exception as e:
            print(e)
        time.sleep(1.)
