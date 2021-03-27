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

conf_cwds = {k:configured_value("panels.%s.cwd" % k, None) for k in ["lock", "launcher", "notifiers"]}

class PanelLauncher:
    def __init__(self, panel):
        self.panel = panel

        self._proc = None

    def get_pid(self):
        try:
            return self._proc.pid
        except:
            return None

    def _start(self):
        self._proc = None

        cmd, cwd = conf_cmds[self.panel](), conf_cwds[self.panel]()
        if cmd is None:
            return

        logger.info("Starting %s in %s", cmd, cwd)
        try:
            self._proc = subprocess.Popen(cmd.split(" "), cwd=cwd)
        except:
            logger.exception("Subprocess")

    def check(self):
        try:
            if self._proc.poll() is not None:
                raise Exception()
        except Exception:
            logger.info("Subprocess for panel %s died", self.panel)
            self._start()

    def stop(self):
        try:
            self._proc.kill()
            self._proc = None
        except:
            pass


class PanelsLauncher(Thread):
    def __init__(self):
        super().__init__()
        self._running = True
        self._panels = [PanelLauncher(k) for k in conf_cmds.keys()]

    def stop(self):
        self._running = False
        for p in self._panels:
            p.stop()

    def get_panel_for_pid(self, pid):
        if pid is None:
            return None

        for p in self._panels:
            parent_pid = p.get_pid()
            if parent_pid is None:
                continue
            if parent_pid == pid:
                return p.panel

            try:
                subprocess.check_output("pstree -aps %d | grep %d" % (pid, parent_pid), shell=True)
                # Successful
                return p.panel
            except:
                # Unsuccessful
                pass
        return None

    def run(self):
        i = 0
        while self._running:
            if i%50 == 0:
                for p in self._panels:
                    p.check()
            i += 1
            time.sleep(.5)

