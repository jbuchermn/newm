import os
import json
import asyncio
import websockets
from threading import Thread

SOCKET_PORT = 8641

class PanelEndpoint(Thread):
    def __init__(self, layout):
        super().__init__()
        self.layout = layout

        self._event_loop = None
        self._server = None

        self._clients = []

        self.start()

    async def _socket_handler(self, client_socket, path):
        print("Opened connection: %s" % path)
        self._clients += [client_socket]
        try:
            async for msg in client_socket:
                try:
                    msg = json.loads(msg)
                    if msg['kind'] == 'launch_app':
                        """
                        Should be LauncherOverlay
                        """
                        self.layout.exit_overlay()
                        os.system("%s &" % msg['app'])
                except Exception:
                    print("Received unparsable message")

        finally:
            print("Closing connection...")
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
        print("Stopping PanelEndpoint...")
        asyncio.run_coroutine_threadsafe(self._stop(), self._event_loop)

    def run(self):
        self._event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._event_loop)

        self._server = websockets.serve(self._socket_handler, "127.0.0.1", SOCKET_PORT)
        self._event_loop.run_until_complete(self._server)
        print("Starting PanelEndpoint...")
        self._event_loop.run_forever()


if __name__ == '__main__':
    from threading import Thread
    import time

    def test():
        global p
        time.sleep(2)
        p.broadcast("Test")
        time.sleep(4)
        p.stop()

    Thread(target=test).start()


    p = PanelEndpoint()
