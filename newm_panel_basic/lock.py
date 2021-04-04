from __future__ import annotations
from typing import Any, Optional

from pyfiglet import Figlet
import curses
import websockets
import json
import asyncio
import time

from newm import SOCKET_PORT
URI = "ws://127.0.0.1:%d" % SOCKET_PORT

class Lock:
    def __init__(self) -> None:
        self.state = "request_user"
        self.ready = False
        self.users = ["jonas", "root"]
        self.selected_user: Optional[str] = "jonas"
        self.message = ""
        self.cred = ""
        self.pending = False

        self.scr = curses.initscr()
        curses.cbreak()
        curses.noecho()
        self.scr.keypad(True)
        curses.curs_set(False)

    def exit(self) -> None:
        curses.curs_set(True)
        self.scr.keypad(False)
        curses.echo()
        curses.endwin()

    def render(self) -> None:
        _, width = self.scr.getmaxyx()


        if self.state == "request_user":
            texts = [
                "",
                "",
                Figlet(font="big", justify="center", width=width).renderText("newm"),
                Figlet(font="digital", justify="center", width=width).renderText("   ".join(self.users)),
                Figlet(font="small", justify="center", width=width).renderText(self.selected_user),
            ]
        elif self.state == "request_cred":
            texts = [
                "",
                "",
                Figlet(font="big", justify="center", width=width).renderText("newm"),
                Figlet(font="digital", justify="center", width=width).renderText(self.message),
                Figlet(font="small", justify="center", width=width).renderText("." * len(self.cred) if not self.pending else "-"),
            ]

        self.scr.erase()
        y = 0
        for t in texts:
            ts = t.split("\n")
            for t in ts:
                self.scr.addstr(y, 0, t)
                y += 1
        self.scr.refresh()


    def enter_cred(self) -> None:
        while True:
            self.render()
            ch = self.scr.getch()
            if ch == curses.KEY_BACKSPACE:
                self.cred = self.cred[:-1] if len(self.cred) > 0 else ""
            elif ch == 10:
                break
            else:
                sch = chr(ch)
                self.cred += sch

    def enter_user(self) -> None:
        while True:
            self.render()
            ch = self.scr.getch()
            if ch == 9:
                try:
                    if self.selected_user is None:
                        self.selected_user = self.users[0] if len(self.users) > 0 else None
                    else:
                        self.selected_user = self.users[(self.users.index(self.selected_user) + 1) % len(self.users)]
                except:
                    pass
            elif ch == 10:
                break


    def process(self, message: Optional[dict[str, Any]]) -> Optional[str]:
        if message is None:
            if self.ready:
                if self.state == "request_cred":
                    self.pending = True
                    self.render()

                    return json.dumps({
                        'kind': 'auth_enter_cred',
                        'cred': self.cred})
                elif self.state == "request_user":
                    self.pending = True
                    self.render()

                    return json.dumps({
                        'kind': 'auth_choose_user',
                        'user': self.selected_user})
        else:
            if message['kind'] == 'auth_request_cred':
                self.state = "request_cred"
                self.message = message['message']
                self.cred = ""
                self.pending = False

                self.ready = False
                self.enter_cred()
                self.ready = True


            elif message['kind'] == 'auth_request_user':
                self.state = "request_user"
                self.users = message['users']
                self.selected_user = self.users[0] if len(self.users) > 0 else None
                self.pending = False

                self.ready = False
                self.enter_user()
                self.ready = True


        return None

def run(lock: Lock) -> None:
    async def _run() -> None:
        try:
            async with websockets.connect(URI) as websocket:
                response = lock.process(None)

                if response is not None:
                    await websocket.send(response)
                else:
                    await websocket.send(json.dumps({ 'kind': 'auth_register' }))

                msg = json.loads(await websocket.recv())
                lock.process(msg)
        except:
            pass

    asyncio.get_event_loop().run_until_complete(_run())


def lock() -> None:
    l = Lock()
    try:
        while True:
            run(l)
            time.sleep(.1)
    finally:
        l.exit()

if __name__ == '__main__':
    lock()
