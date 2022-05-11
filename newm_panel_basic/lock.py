from __future__ import annotations
from typing import Any, Optional

from pyfiglet import Figlet
import os
import curses
import json
import asyncio
import time
import logging

from newm import connect_to_auth

logger = logging.getLogger(__name__)

class Lock:
    def __init__(self) -> None:
        self.state = "initial"
        self.users: list[str] = []
        self.selected_user: Optional[str] = None
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


        if self.state == "initial":
            texts = [
                "",
                "",
                Figlet(font="big", justify="center", width=width).renderText("newm"),
                Figlet(font="digital", justify="center", width=width).renderText("Initial state")
            ]
        elif self.state == "request_user":
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

    def reset(self) -> None:
        self.scr.clear()
        self.render()

    def enter_cred(self) -> None:
        while True:
            self.render()
            ch = self.scr.getch()
            if ch == curses.ERR or ch == 410:  # 410 is returned on resize
                continue
            if ch == curses.KEY_BACKSPACE:
                self.cred = self.cred[:-1] if len(self.cred) > 0 else ""
            elif ch == 10:
                break
            else:
                try:
                    sch = chr(ch)
                    self.cred += sch
                except:
                    logger.exception("enter_cred")

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


    def __call__(self, message: dict[str, Any]) -> dict[str, Any]:
        if message['kind'] == 'auth_request_cred':
            self.state = "request_cred"
            self.message = message['message']
            self.cred = ""
            self.pending = False

            self.enter_cred()

            return {'kind': 'auth_enter_cred',
                    'cred': self.cred}


        elif message['kind'] == 'auth_request_user':
            self.state = "request_user"
            self.users = message['users']
            self.selected_user = self.users[0] if len(self.users) > 0 else None
            self.pending = False

            self.enter_user()

            return {'kind': 'auth_choose_user',
                    'user': self.selected_user}

        else:
            logger.warn("Unsupported message %s" % message)
            return { 'error': 'Unsupported' }



def lock() -> None:
    l = Lock()
    try:
        while True:
            logger.debug("Main loop...")
            try:
                l.reset()
                connect_to_auth(l)
            except:
                logger.exception("Excpetion in main loop")
            time.sleep(.1)
    finally:
        l.exit()

if __name__ == '__main__':
    lock()
