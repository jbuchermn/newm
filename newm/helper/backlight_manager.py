from __future__ import annotations
from typing import Callable

import logging
import time
import os

from .execute import execute

logger = logging.getLogger(__name__)

class BacklightManager:
    def __init__(self, commands: tuple[str, str, Callable[[int], str]]=("brightnessctl m", "brightnessctl g", lambda v: "brightnessctl s %d" % v),
            dim_factors: tuple[float, float]=(0.5, 0.33),
            anim_time: float=0.3) -> None:
        self._commands = commands
        self._dim_factors = dim_factors
        self._anim_time = anim_time

        self._current = 0
        self._max = 1
        self._enabled = True
        try:
            self._current = int(execute(self._commands[1]))
            self._max = int(execute(self._commands[0]))
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
        os.system(self._commands[2](self._current) + " &")

    def callback(self, code: str) -> None:
        if code == "sleep":
            self._current = 1 # If set to zero, systemd will resume with 100%
            self._next = 1
            execute(self._commands[2](self._current))
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
        self._next = next

    def adjust(self, factor: float) -> None:
        if self._predim < .3*self._max and factor > 1.:
            self._predim += round(.1*self._max)
        else:
            self._predim = max(0, min(self._max, round(self._predim * factor)))
        self._next = self._predim

        self._anim_ts = time.time(), time.time() + self._anim_time, 0
