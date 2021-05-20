from __future__ import annotations
from typing import Optional, cast

from threading import Thread
import subprocess
import time
import logging
from .config import configured_value

logger = logging.getLogger(__name__)

conf_cmds = {
    'lock': configured_value("panels.lock.cmd", "alacritty -e newm-panel-basic lock"),
    'launcher': configured_value("panels.launcher.cmd", None),
    'notifiers': configured_value("panels.notifiers.cmd", None)
}

conf_cwds = {k: configured_value("panels.%s.cwd" % k, cast(Optional[str], None)) for k in ["lock", "launcher", "notifiers"]}

class PanelLauncher:
    def __init__(self, panel: str) -> None:
        self.panel = panel

        self._proc: Optional[subprocess.Popen] = None

    def get_pid(self) -> Optional[int]:
        if self._proc is not None:
            return self._proc.pid
        else:
            return None

    def _start(self) -> None:
        self._proc = None

        cmd, cwd = conf_cmds[self.panel](), conf_cwds[self.panel]()
        if cmd is None:
            return

        logger.info("Starting %s in %s", cmd, cwd)
        try:
            self._proc = subprocess.Popen(cmd.split(" "), cwd=cwd)
        except:
            logger.exception("Subprocess")

    def check(self) -> None:
        try:
            if self._proc is None or self._proc.poll() is not None:
                raise Exception()
        except Exception:
            logger.info("Subprocess for panel %s died", self.panel)
            self._start()

    def stop(self) -> None:
        try:
            if self._proc is not None:
                self._proc.kill()
            self._proc = None
        except:
            pass


class PanelsLauncher(Thread):
    def __init__(self) -> None:
        super().__init__()
        self._running = True
        self._panels = [PanelLauncher(k) for k in conf_cmds.keys()]

    def stop(self) -> None:
        self._running = False
        for p in self._panels:
            p.stop()

    def get_panel_for_pid(self, pid: int) -> Optional[str]:
        if pid is None:
            return None

        for p in self._panels:
            parent_pid = p.get_pid()
            if parent_pid is None:
                continue
            if parent_pid == pid:
                return p.panel

            try:
                subprocess.check_output("pstree -aps %d | grep \",%d$\"" % (pid, parent_pid), shell=True)
                # Successful
                return p.panel
            except:
                # Unsuccessful
                pass
        return None

    def run(self) -> None:
        i = 0
        while self._running:
            if i%50 == 0:
                for p in self._panels:
                    p.check()
            i += 1
            time.sleep(.5)

