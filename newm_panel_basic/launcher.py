from __future__ import annotations
from typing import Any, Optional

import os
import sys
import curses
import logging
import pathlib
import importlib
from pyfiglet import Figlet  # type: ignore
from fuzzywuzzy import process  # type: ignore

logger = logging.getLogger(__name__)


def _launcher() -> None:
    # Title to Command
    entries: dict[str, str] = {}

    # Key to (Title, Command)
    shortcuts: dict[int, tuple[str, str]] = {}

    home = os.environ['HOME'] if 'HOME' in os.environ else '/'
    path = pathlib.Path(home) / '.config' / 'newm' / 'launcher.py'

    if not path.is_file():
        path = pathlib.Path('/etc') / 'newm' / 'launcher.py'

    if path.is_file():
        logger.info("Loading config at %s", path)

        module = path.stem

        try:
            del sys.modules[module]
        except KeyError:
            pass

        sys.path.insert(0, str(path.parent))
        res = importlib.import_module(module).__dict__
        if 'entries' in res:
            entries = res['entries']
        if 'shortcuts' in res:
            shortcuts = res['shortcuts']

    def list_suggestions(search: str) -> list[tuple[str, str]]:
        if search == "":
            return []
        logger.debug("Extracting '%s'" % search)
        result = process.extract(search, list(entries.keys()), limit=10)
        return [(k[0], entries[k[0]]) for k in result if k[1] > 40]

    def render(scr: Any, search: str) -> None:
        suggestions = list_suggestions(search)
        logger.debug("%s -> %s", search, suggestions)

        _, width = scr.getmaxyx()
        texts = [
            "",
            Figlet(font="big", justify="center", width=width).renderText("newm"),
            Figlet(font="digital", justify="center", width=width).renderText("   ".join(["%d %s" % (k, v[0]) for k, v in shortcuts.items()])),
            "    > " + search] + [
                ("    + " if i == 0 else "      ") + t[0] for i, t in enumerate(suggestions)
            ]

        scr.erase()
        y = 0
        for t in texts:
            ts = t.split("\n")
            for t in ts:
                scr.addstr(y, 0, t)
                y += 1
        scr.refresh()

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
                if ch == curses.ERR or ch == 410:  # 410 is returned on resize
                    continue
                if ch == curses.KEY_BACKSPACE:
                    search = search[:-1] if len(search) > 0 else ""
                elif ch == 10:
                    break
                elif ch == 27:
                    logger.debug("Unexpected - got escape")
                else:
                    try:
                        sch = chr(ch)
                        search += sch
                    except:
                        logger.exception("enter")

                try:
                    _ = int(search)
                    break
                except:
                    pass

            try:
                cmd = shortcuts[int(search)][1]
                logger.debug("Executing %s" % cmd)
                os.system("newm-cmd launcher %s > /dev/null" % cmd)
                continue
            except:
                pass

            suggestions = list_suggestions(search)
            if len(suggestions) > 0:
                logger.debug("Executing %s" % suggestions[0][1])
                os.system("newm-cmd launcher %s > /dev/null" % suggestions[0][1])


    finally:
        curses.curs_set(True)
        scr.keypad(False)
        curses.echo()
        curses.endwin()

def launcher() -> None:
    while True:
        try:
            _launcher()
        except:
            pass
