from __future__ import annotations
from typing import Union, Callable, Optional

import time
import logging
from threading import Thread

from .provider import GestureProvider
from ..gesture import Gesture

logger = logging.getLogger(__name__)

class CGestureProvider(GestureProvider, Thread):
    def __init__(self, on_gesture: Callable[[Gesture], bool]) -> None:
        Thread.__init__(self)
        GestureProvider.__init__(self, on_gesture)
        self._captured: Optional[Gesture] = None

        self._running = True

        # TODO: Configure
        self._scale = 1000.

        self._reference = (0., 0.)
        self._d2s = 0.
        self._active: Optional[bool] = None

    def start(self) -> None:
        Thread.start(self)

    def run(self) -> None:
        while self._running:
            time.sleep(.25)
            if self._active == True:
                self._active = False
            elif self._active == False:
                self._finish()

    def stop(self) -> None:
        self._running = False

    def _start(self, n: int) -> int:
        if self._captured is not None:
            return 2

        gesture = Gesture("swipe-%d" % n if n > 1 else "move-1")
        if self._on_gesture(gesture):
            self._captured = gesture
            self._reference = (0., 0.)
            self._d2s = 0.
            return 2
        return 0

    def _update(self, delta_x: float, delta_y: float) -> int:
        if self._captured is None:
            return 0

        delta_x /= self._scale
        delta_y /= self._scale

        self._reference = self._reference[0] + delta_x, self._reference[1] + delta_y
        self._d2s += delta_x**2 + delta_y**2

        self._captured._update({ "delta_x": self._reference[0], "delta_y": self._reference[1], "delta2_s": self._d2s })
        return 2

    def _finish(self) -> int:
        if self._captured is not None:
            self._captured._terminate()
            self._captured = None
            self._active = None
            return 2
        else:
            return 0

    def on_pywm_gesture(self, kind: str, time_msec: int, args: list[Union[float, int]]) -> int:
        if kind != "swipe":
            return self._finish()

        if args[0] == 0:
            return self._finish()
        else:
            if len(args) == 1:
                return self._start(int(args[0]))
            else:
                return self._update(float(args[1]), float(args[2]))

    def on_pywm_motion(self, time_msec: int, delta_x: float, delta_y: float) -> int:
        self._start(1)
        self._active = True
        return self._update(delta_x, delta_y)

    def on_pywm_axis(self, time_msec: int, source: int, orientation: int, delta: float, delta_discrete: int) -> int:
        self._start(2)
        self._active = True
        # TODO: Assumes natural scrolling
        return self._update(-delta if orientation == 1 else 0., -delta if orientation == 0 else 0.)
