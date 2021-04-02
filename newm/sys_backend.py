from __future__ import annotations
from typing import Callable, Any, TYPE_CHECKING, Optional

from threading import Thread
import os
import time
import psutil # type: ignore
import logging

if TYPE_CHECKING:
    from .layout import Layout

logger = logging.getLogger(__name__)

class SysBackendEndpoint:
    def __init__(self, name: str, setter: Callable[[float], Any], getter: Callable[[], float]):
        self.name = name
        self._setter = setter
        self._getter = getter

    def set(self, value: float) -> None:
        self._setter(value)

    def get(self) -> float:
        return self._getter()

class SysBackendEndpoint_sysfs(SysBackendEndpoint):
    def __init__(self, name: str, path: str, max_path: str):
        self._path = path
        self._max_path = max_path

        super().__init__(name, self._set, self._get)

    def _set(self, value: float) -> None:
        max_val = int(open(self._max_path, 'r').read()[:-1])
        val = value * max_val
        val = max(min(max_val, val), 0)

        open(self._path, 'w').write("%d" % val)

    def _get(self) -> float:
        val = int(open(self._path, 'r').read()[:-1])
        max_val = int(open(self._max_path, 'r').read()[:-1])
        return float(val) / max_val

class SysBackendEndpoint_alsa(SysBackendEndpoint):
    def __init__(self, name: str):
        super().__init__(name, self._set, self._get)

    def _set(self, value: float) -> None:
        os.system("amixer sset Master %d%%" % int(value * 100))

    def _get(self) -> float:
        val = int(os.popen("amixer sget Master | grep 'Mono:'").read().split('[')[1].split('%]')[0])
        return val / 100.


class SysBackend(Thread):
    def __init__(self, wm: Layout):
        super().__init__()
        self.wm = wm
        self._endpoints: dict[str, SysBackendEndpoint] = {}
        self._idle_backup: Optional[dict[str, float]] = None
        self._idle_backup_for = 0

        self._running = True
        self.start()

    def set_endpoints(self, *endpoints: SysBackendEndpoint) -> None:
        self._endpoints = {e.name: e for e in endpoints}

    def run(self) -> None:
        while self._running:
            time.sleep(1.)
            bat = psutil.sensors_battery()
            if bat.percent < 15 and not bat.power_plugged:
                self.wm.panel_endpoint.broadcast({
                    'kind': 'sys_backend',
                    'battery': bat.percent / 100.
                })

    def stop(self) -> None:
        self._running = False

    def adjust(self, name: str, action: Callable[[float], float], broadcast: bool=True) -> None:
        try:
            e = self._endpoints[name]
            val = e.get()
            new_val = action(val)
            e.set(new_val)
            new_val = e.get()
            logger.debug("SysBackend: set %s %f -> %f", name, val, new_val);

            if broadcast:
                self.wm.panel_endpoint.broadcast({
                    'kind': 'sys_backend',
                    name: new_val
                })

        except KeyError:
            logger.debug("Skipping %s", name)
        except:
            logger.exception("Adjust")

    def idle_state(self, level: int) -> None:
        """
        level == 0 (active), 1 (idle), 2 (turn monitor off)
        """
        if level == 0:
            if self._idle_backup is not None:
                for k, v in self._idle_backup.items():
                    self.adjust(k, lambda _: v, broadcast=k=="backlight")
                self._idle_backup = None
                self._idle_backup_for = 0
        elif level == 1:
            if self._idle_backup_for != 1:
                self._idle_backup = {k:v.get() for k,v in self._endpoints.items() if k in ["backlight", "kbdlight"]}
                self._idle_backup_for = 1
                self.adjust("kbdlight", lambda v: v*0.5, broadcast=False)
                self.adjust("backlight", lambda v: v*0.5)
        elif level == 2:
            if self._idle_backup_for != 2:
                if self._idle_backup_for != 1:
                    self._idle_backup = {k:v.get() for k,v in self._endpoints.items() if k in ["backlight", "kbdlight"]}
                self._idle_backup_for = 2
                self.adjust("kbdlight", lambda _: 0, broadcast=False)
                self.adjust("backlight", lambda _: 0)


    def register_xf86_keybindings(self) -> None:
        self.wm.key_processor.register_bindings(
            ("XF86MonBrightnessUp", lambda: self.adjust('backlight', lambda v: v + 0.1)),
            ("XF86MonBrightnessDown", lambda: self.adjust(
                'backlight',
                lambda v: 0 if abs(v - 0.01) < 0.01 else max(0.01, v - 0.1))),
            ("XF86LaunchA", lambda: logger.info("LaunchA")),
            ("XF86LaunchB", lambda: logger.info("LaunchB")),
            ("XF86KbdBrightnessUp", lambda: self.adjust('kbdlight', lambda v: v + 0.1)),
            ("XF86KbdBrightnessDown", lambda: self.adjust('kbdlight', lambda v: v - 0.1)),
            ("XF86AudioPrev", lambda: logger.info("AudioPrev")),
            ("XF86AudioPlay", lambda: logger.info("AudioPlay")),
            ("XF86AudioNext", lambda: logger.info("AudioNext")),
            ("XF86AudioMute", lambda: self.adjust('volume', lambda _: 0)),
            ("XF86AudioLowerVolume", lambda: self.adjust("volume", lambda v: v - 0.1)),
            ("XF86AudioRaiseVolume", lambda: self.adjust("volume", lambda v: v + 0.1))
        )


