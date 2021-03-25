import os
import json
import asyncio
import websockets
import logging
from threading import Thread

SOCKET_PORT = 8641

logger = logging.getLogger(__name__)

class PanelEndpoint(Thread):
    def __init__(self, layout):
        super().__init__()
        self.layout = layout

        self._event_loop = None
        self._server = None

        self._clients = []

    async def _socket_handler(self, client_socket, path):
        logger.info("Opened connection: %s" % path)
        self._clients += [client_socket]
        try:
            async for msg in client_socket:
                try:
                    msg = json.loads(msg)
                    if msg['kind'] == 'launch_app':
                        self.layout.launch_app(msg['app'])

                    elif msg['kind'] == 'cmd':
                        result = self.layout.command(msg['cmd'])
                        await client_socket.send(json.dumps({ 'msg': str(result) }))

                    elif msg['kind'].startswith('auth_'):
                        self.layout.auth_backend.on_message(msg)
                except Exception:
                    logger.debug("Received unparsable message: %s", msg)

        finally:
            logger.info("Closing connection: %s", path)
            self._clients.remove(client_socket)


    async def _broadcast(self, msg):
        for c in self._clients:
            try:
                await c.send(json.dumps(msg))
            except:
                pass

    def broadcast(self, msg):
        asyncio.run_coroutine_threadsafe(self._broadcast(msg), self._event_loop)

    async def _stop(self):
        self._event_loop.stop()

    def stop(self):
        logger.info("Stopping PanelEndpoint...")
        asyncio.run_coroutine_threadsafe(self._stop(), self._event_loop)

    def run(self):
        self._event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._event_loop)

        self._server = websockets.serve(self._socket_handler, "127.0.0.1", SOCKET_PORT)
        self._event_loop.run_until_complete(self._server)
        logger.info("Starting PanelEndpoint...")
        self._event_loop.run_forever()


def msg(message):
    async def _send():
        uri = "ws://127.0.0.1:%d" % SOCKET_PORT
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps({ 'kind': 'cmd', 'cmd': message }))
            response = json.loads(await websocket.recv())
            if 'msg' in response:
                print(response['msg'])

    asyncio.get_event_loop().run_until_complete(_send())


if __name__ == '__main__':
    # msg("lock")

    from threading import Thread
    import time

    def test():
        global p
        time.sleep(2)
        p.broadcast("Test")
        time.sleep(4)
        p.stop()

    Thread(target=test).start()


    p = PanelEndpoint(None)
