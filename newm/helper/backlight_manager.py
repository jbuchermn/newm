from __future__ import annotations
from typing import Callable

import logging
import time

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
        self._anim_ts = 0., 0.

    def update(self) -> None:
        if self._anim_ts[0] == 0.:
            return
        t = time.time()
        if t > self._anim_ts[1]:
            self._current = self._next
            self._anim_ts = 0., 0.
        else:
            self._current = int(self._current + (self._next - self._current)/(self._anim_ts[1] - self._anim_ts[0])*(t - self._anim_ts[0]))
        execute(self._commands[2](self._current) + " &")

    def callback(self, code: str) -> None:
        if code in ["lock", "idle-lock"]:
            self._next = int(self._predim * self._dim_factors[0])
        elif code == "idle":
            self._next = int(self._predim * self._dim_factors[1])
        elif code == "active":
            self._next = self._predim

        self._anim_ts = time.time(), time.time() + self._anim_time

    def adjust(self, factor: float) -> None:
        if self._predim < .3*self._max and factor > 1.:
            self._predim += int(.1*self._max)
        else:
            self._predim = max(0, min(self._max, int(self._predim * factor)))
        self._next = self._predim

        self._anim_ts = time.time(), time.time() + self._anim_time
