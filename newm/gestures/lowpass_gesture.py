from __future__ import annotations
from typing import Optional

from threading import Thread
import time

from .lowpass import Lowpass
from .gesture import Gesture
from .gesture_listener import GestureListener

class LowpassGesture(Thread, Gesture):
    def __init__(self, gesture: Gesture, lp_inertia: float, lp_freq: float):
        Thread.__init__(self)
        Gesture.__init__(self, gesture.kind)

        self.gesture = gesture

        gesture.listener(GestureListener(
            self.on_update,
            self.on_terminate
        ))

        self._lp_inertia = lp_inertia
        self._lp_freq = lp_freq
        self._lp: dict[str, Lowpass] = {}
        self._values: Optional[dict[str, float]] = None
        self._running = True
        self.start()

    def on_update(self, values: dict[str, float]) -> None:
        self._values = values

    def on_terminate(self) -> None:
        self._running = False
        self.join()

        self._terminate()

    def run(self) -> None:
        while self._running:
            if self._values is not None:
                lp_values = {}
                for k in self._values:
                    if k not in self._lp:
                        self._lp[k] = Lowpass(self._lp_inertia)
                    lp_values[k] = self._lp[k].next(self._values[k])
                self._update(lp_values)
            time.sleep(1./self._lp_freq)
