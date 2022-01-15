from __future__ import annotations
from typing import Optional

import logging
import time
import os

from .execute import execute
from .bar_display import BarDisplay

logger = logging.getLogger(__name__)

class BacklightManager:
    def __init__(self, dim_factors: tuple[float, float]=(0.5, 0.33), anim_time: float=0.3, display: Optional[BarDisplay]=None) -> None:
        self._dim_factors = dim_factors
        self._anim_time = anim_time
        self._display = display

        self._current = 0
        self._max = 1
        self._enabled = True
        try:
            self._current = self._get_current()
            self._max = self._get_max()
        except Exception:
            logger.exception("Disabling BacklightManager")
            self._enabled = False

        self._predim = self._current
        self._next = self._current
        self._anim_ts = -1., -1., -1.

    def update(self) -> None:
        if not self._enabled or self._anim_ts[0] < 0.:
            return

        t = time.time()

        dt = t - self._anim_ts[2]
        if dt > 1. / 30.:
            self._anim_ts = self._anim_ts[0], self._anim_ts[1], t
        else:
            return

        if t > self._anim_ts[1]:
            self._current = self._next
            self._anim_ts = -1., -1., -1.
        else:
            self._current = round(self._current + (self._next - self._current)/(self._anim_ts[1] - self._anim_ts[0])*(t - self._anim_ts[0]))
        self._set(self._current)

    def callback(self, code: str) -> None:
        if code == "sleep":
            self._current = 1 # If set to zero, systemd will resume with 100%
            self._next = 1
            self._set(self._current)
            return

        next = self._next
        if code == "wakeup":
            next = self._predim
        elif code in ["lock", "idle-lock"]:
            next = round(self._predim * self._dim_factors[0])
        elif code == "idle":
            next = round(self._predim * self._dim_factors[1])
        elif code == "idle-presuspend":
            next = 0
        elif code == "active":
            next = self._predim

        if abs(next - self._next) > 0.5 and self._anim_ts[0] < 0:
            t = time.time()
            self._anim_ts = t, t + self._anim_time, 0.

            if self._display is not None:
                self._display.display(next / self._max)
        self._next = next

    def get(self) -> float:
        return self._predim / self._max

    def set(self, value: float) -> None:
        self._predim = max(0, min(self._max, int(self._max * value)))
        self._next = self._predim

        self._anim_ts = time.time(), time.time() + self._anim_time, 0

        if self._display is not None:
            self._display.display(self._next / self._max)

    """
    Override these to configure command and device
    """
    def _get_max(self) -> int:
        return int(execute("brightnessctl m"))

    def _get_current(self) -> int:
        return int(execute("brightnessctl g"))

    def _set(self, val: int) -> None:
        os.system("brightnessctl s %d > /dev/null &" % self._current)
