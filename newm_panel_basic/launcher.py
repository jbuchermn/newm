from __future__ import annotations
from typing import Any, Optional, Generator

import os
import time
import curses
import logging
from fuzzywuzzy import process

logger = logging.getLogger(__name__)



entries: dict[str, str] = {}
shortcuts: dict[int, str] = {}

# TODO Read from ~/.config/newm/launcher.py
entries["chromium"] = "chromium --enable-features=UseOzonePlatform --ozone-platform=wayland"
entries["firefox"] = "MOZ_ENABLE_WAYLAND=1 firefox"
shortcuts[1] = "chromium --enable-features=UseOzonePlatform --ozone-platform=wayland"


def launcher() -> None:
    def list_suggestions(search: str) -> list[tuple[str, str]]:
        if search == "":
            return []
        result = process.extract(search, list(entries.keys()), limit=10)
        logger.debug(result)
        return [(k[0], entries[k[0]]) for k in result]

    def render(scr: Any, search: str) -> None:
        suggestions = list_suggestions(search)
        logger.debug("%s -> %s", search, suggestions)
        # TODO
        # Figlet title
        # Shortcuts
        # Fuzzy search

    scr = curses.initscr()
    try:
        curses.cbreak()
        curses.noecho()
        scr.keypad(True)
        curses.curs_set(False)

        while True:
            search = ""
            while True:
                render(scr, search)
                ch = scr.getch()
                if ch == curses.KEY_BACKSPACE:
                    search = search[:-1] if len(search) > 0 else ""
                elif ch == 10:
                    break
                else:
                    try:
                        sch = chr(ch)
                        search += sch
                    except:
                        logger.exception("enter_cred")

                try:
                    _ = int(search)
                    break
                except:
                    pass

            try:
                cmd = shortcuts[int(search)]
                os.system("newm-cmd launcher %s" % cmd)
                continue
            except:
                logger.exception("shortcuts")

            suggestions = list_suggestions(search)
            if len(suggestions) > 0:
                os.system("newm-cmd launcher %s" % suggestions[0][1])


    finally:
        curses.curs_set(True)
        scr.keypad(False)
        curses.echo()
        curses.endwin()
