from __future__ import annotations
from typing import Union, Callable, Optional

import logging

from .provider import GestureProvider
from ..gesture import Gesture

logger = logging.getLogger(__name__)

"""
At the moment libinput is not able to properly handle gestures at all, e.g. any two-finger gesture which is not
very explicitly pinch, does not get reported at all - maybe some day this changes.
"""
class CGestureProvider(GestureProvider):
    def __init__(self, on_gesture: Callable[[Gesture], bool]) -> None:
        super().__init__(on_gesture)
        self._captured: Optional[Gesture] = None

        self._scale = 1000.
        self._reference = (0., 0.)

    def on_pywm_gesture(self, kind: str, time_msec: int, args: list[Union[float, str]]) -> int:
        if kind != "swipe":
            self._captured = None
            return 0

        if args[0] == 0:
            if self._captured is not None:
                self._captured._terminate()
                self._captured = None
                return 2
        else:
            if self._captured is None and len(args) == 1:
                gesture = Gesture("swipe-%d" % int(args[0]))
                if self._on_gesture(gesture):
                    self._captured = gesture
                    self._reference = (0., 0.)
                    return 2
            elif self._captured is not None and len(args) == 3:
                delta_x = float(args[1]) / self._scale
                delta_y = float(args[2]) / self._scale
                self._reference = self._reference[0] + delta_x, self._reference[1] + delta_y

                self._captured._update({ "delta_x": self._reference[0], "delta_y": self._reference[1] })
                return 2

        return 1

    def on_pywm_motion(self, time_msec: int, delta_x: float, delta_y: float) -> int:
        return 2 if self._captured is not None else 0

    def on_pywm_axis(self, time_msec: int, source: int, orientation: int, delta: float, delta_discrete: int) -> int:
        return 2 if self._captured is not None else 0
