from __future__ import annotations
from typing import Any, Optional

from pyfiglet import Figlet
import curses
import websockets
import json
import asyncio
import time

from newm import SOCKET_PORT

class Lock:
    def __init__(self) -> None:
        self.state = "request_user"
        self.users = ["jonas", "root"]
        self.selected_user: Optional[str] = "jonas"
        self.message = ""
        self.cred = ""

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
                Figlet(font="bubble", justify="center", width=width).renderText("   ".join(self.users)),
                Figlet(font="small", justify="center", width=width).renderText(self.selected_user),
            ]
        elif self.state == "request_cred":
            texts = [
                "",
                "",
                Figlet(font="big", justify="center", width=width).renderText("newm"),
                Figlet(font="5lineoblique", justify="center", width=width).renderText(self.message),
                Figlet(font="small", justify="center", width=width).renderText("." * len(self.cred)),
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
        try:
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
        except:
            pass

    def enter_user(self) -> None:
        try:
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
        except:
            pass


    def process(self, message: dict[str, Any]) -> Optional[str]:
        if message['kind'] == 'auth_request_cred':
            self.state = "request_cred"
            self.message = message['message']
            self.cred = ""

            self.enter_cred()

            return self.cred
        elif message['kind'] == 'auth_request_user':
            self.state = "request_user"
            self.users = message['users']
            self.selected_user = self.users[0] if len(self.users) > 0 else None

            self.enter_user()

            return self.selected_user

        return None



def run(lock: Lock) -> None:
    async def _run() -> None:
        uri = "ws://127.0.0.1:%d" % SOCKET_PORT
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps({ 'kind': 'auth_register' }))


            while True:
                response = json.loads(await websocket.recv())
                if response['kind'] == 'auth_request_cred':
                    await websocket.send(json.dumps({
                        'kind': 'auth_enter_cred',
                        'cred': lock.process(response)}))

                elif response['kind'] == 'auth_request_user':
                    await websocket.send(json.dumps({
                        'kind': 'auth_choose_user',
                        'user': lock.process(response)}))
                else:
                    break

    asyncio.get_event_loop().run_until_complete(_run())


def lock() -> None:
    l = Lock()
    while True:
        try:
            run(l)
        except Exception as e:
            print(e)
        time.sleep(1.)
    l.exit()

if __name__ == '__main__':
    lock()
