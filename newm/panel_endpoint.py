from __future__ import annotations
from typing import Any, TYPE_CHECKING, Optional

from asyncio.events import AbstractEventLoop
import os
import json
import asyncio
import websockets
import logging
from threading import Thread


if TYPE_CHECKING:
    from websockets.server import Serve, WebSocketServerProtocol
    from .layout import Layout

SOCKET_PORT = 8641

logger = logging.getLogger(__name__)

class PanelEndpoint(Thread):
    def __init__(self, layout: Layout):
        super().__init__()
        self.layout = layout

        self._event_loop: Optional[AbstractEventLoop] = None
        self._server: Optional[Serve] = None

        self._clients: list[WebSocketServerProtocol] = []

    async def _socket_handler(self, client_socket: WebSocketServerProtocol, path: str) -> None:
        logger.info("Opened connection: %s" % path)
        self._clients += [client_socket]
        try:
            async for bmsg in client_socket:
                try:
                    msg = json.loads(bmsg)
                    if msg['kind'] == 'launch_app':
                        self.layout.launch_app(msg['app'])
                        await client_socket.send(json.dumps({ 'msg': "OK" }))

                    elif msg['kind'] == 'cmd':
                        result = self.layout.command(msg['cmd'])
                        await client_socket.send(json.dumps({ 'msg': str(result) }))

                    elif msg['kind'].startswith('auth_'):
                        self.layout.auth_backend.on_message(msg)
                except Exception:
                    logger.exception("Received unparsable message: %s", bmsg)

        finally:
            logger.info("Closing connection: %s", path)
            self._clients.remove(client_socket)


    async def _broadcast(self, msg: Any) -> None:
        try:
            logger.debug("Broadcasting %s to %s", json.dumps(msg), self._clients)
        except:
            pass
        
        for c in self._clients:
            try:
                await c.send(json.dumps(msg))
            except:
                logger.exception("broadcast")

    def broadcast(self, msg: Any) -> None:
        if self._event_loop is not None:
            asyncio.run_coroutine_threadsafe(self._broadcast(msg), self._event_loop)

    async def _stop(self) -> None:
        if self._event_loop is not None:
            self._event_loop.stop()

    def stop(self) -> None:
        if self._event_loop is not None:
            logger.info("Stopping PanelEndpoint...")
            asyncio.run_coroutine_threadsafe(self._stop(), self._event_loop)

    def run(self) -> None:
        self._event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._event_loop)

        self._server = websockets.serve(self._socket_handler, "127.0.0.1", SOCKET_PORT)
        self._event_loop.run_until_complete(self._server)
        logger.info("Starting PanelEndpoint...")
        self._event_loop.run_forever()


def msg(dct: dict[str, Any]) -> None:
    async def _send() -> None:
        uri = "ws://127.0.0.1:%d" % SOCKET_PORT
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps(dct))
            response = json.loads(await websocket.recv())
            if 'msg' in response and response['msg'] != "None":
                print(response['msg'])

    asyncio.get_event_loop().run_until_complete(_send())


if __name__ == '__main__':
    SOCKET_DEBUG_PORT = SOCKET_PORT + 1
    clients = []

    async def send(msg: Any) -> None:
        global clients
        for c in clients:
            try:
                await c.send(json.dumps(msg))
            except:
                logger.exception("broadcast")

    async def socket_handler(client_socket: WebSocketServerProtocol, path: str) -> None:
        global clients
        print("Opened connection: %s" % path)
        clients += [client_socket]
        try:
            async for bmsg in client_socket:
                try:
                    msg = json.loads(bmsg)
                    print(msg)
                    if msg['kind'] == 'auth_register':
                        await send({'kind': 'auth_request_cred', 'user': 'jonas', 'message': 'Password?'})
                    elif msg['kind'] == 'auth_enter_cred':
                        await send({'kind': 'auth_request_cred', 'user': 'jonas', 'message': 'Password?'})
                except Exception:
                    print("Received unparsable message: %s", bmsg)

        finally:
            print("Closing connection: %s" % path)
            clients.remove(client_socket)

    print("Starting debug PanelEndpoint...")
    server = websockets.serve(socket_handler, "127.0.0.1", SOCKET_DEBUG_PORT)
    asyncio.get_event_loop().run_until_complete(server)
    asyncio.get_event_loop().run_forever()

