from __future__ import annotations
from typing import Optional, Union

from abc import abstractmethod

import logging
import time
from threading import Thread
import math
from typing import Callable

from ...config import configured_value
from ..gesture import Gesture
from ..gesture_listener import GestureListener
from .provider import GestureProvider

from .pyevdev_touchpad import find_all_touchpads, Touchpad, TouchpadUpdate

logger = logging.getLogger(__name__)

conf_two_finger_min_dist = configured_value('gestures.pyevdev.two_finger_min_dist', .1)
conf_validate_threshold = configured_value('gestures.pyevdev.validate_threshold', .02)

def get_validate_center(kind: str) -> float:
    if kind == 'scale':
        return 1.
    return 0.

def get_validate_threshold(kind: str) -> float:
    if kind == 'delta2_s':
        return conf_validate_threshold()**2
    return conf_validate_threshold()

class PyEvdevGesture(Gesture):
    def __init__(self, kind: str, parent: Gestures) -> None:
        super().__init__(kind)
        self.parent = parent
        self.pending = True

        self._offset: Optional[dict[str, float]] = None

    def update(self, values: dict[str, float]) -> None:
        if self.pending:
            validate = False
            for k in values:
                v = values[k]
                if abs(v - get_validate_center(k)) > get_validate_threshold(k):
                    validate = True
                    break

            if validate:
                self._offset = {k: values[k] - get_validate_center(k)
                                for k in values}
                self.pending = False

        if not self.pending and self._offset is not None:
            self._update({k: values[k] - self._offset[k] for k in values})

    @abstractmethod
    def process(self, update: TouchpadUpdate) -> bool:
        """
        Returns false if the update terminates the gesture
        """
        pass


class SingleFingerMoveGesture(PyEvdevGesture):
    def __init__(self, parent: Gestures, update: TouchpadUpdate) -> None:
        super().__init__("move-1", parent)

        assert(update.n_touches == 1 and len(update.touches) == 1)
        self._initial_x = update.touches[0][1]
        self._initial_y = update.touches[0][2]

    def process(self, update: TouchpadUpdate) -> bool:
        if update.n_touches != 1 or len(update.touches) != 1:
            return False

        self.update({
            'delta_x': update.touches[0][1] - self._initial_x,
            'delta_y': update.touches[0][2] - self._initial_y,
        })
        return True

    def __str__(self) -> str:
        return "SingleFingerMove"


class TwoFingerSwipePinchGesture(PyEvdevGesture):
    def __init__(self, parent: Gestures, update: TouchpadUpdate):
        super().__init__("swipe-2", parent)

        assert(update.n_touches == 2 and len(update.touches) == 2)
        self._initial_cog_x, \
            self._initial_cog_y, \
            self._initial_dist = self._process(update)

    def _process(self, update: TouchpadUpdate) -> tuple[float, float, float]:
        cog_x = sum([x for _, x, _, _ in update.touches]) / 2.
        cog_y = sum([y for _, _, y, _ in update.touches]) / 2.
        dist = math.sqrt(
            (update.touches[0][1] - update.touches[1][1])**2 +
            (update.touches[0][2] - update.touches[1][2])**2
        )

        return cog_x, cog_y, max(conf_two_finger_min_dist(), dist)

    def process(self, update: TouchpadUpdate) -> bool:
        if update.n_touches != 2:
            return False

        if len(update.touches) != 2:
            return True

        cog_x, cog_y, dist = self._process(update)
        self.update({
            'delta_x': cog_x - self._initial_cog_x,
            'delta_y': cog_y - self._initial_cog_y,
            'scale': dist/self._initial_dist
        })

        return True

    def __str__(self) -> str:
        return "TwoFingerSwipePinch"


class HigherSwipeGesture(PyEvdevGesture):
    def __init__(self, parent: Gestures, update: TouchpadUpdate) -> None:
        super().__init__("swipe-%d" % update.n_touches, parent)

        assert(update.n_touches in [3, 4, 5])

        self.n_touches = update.n_touches
        self._touchpad_update = update
        self._begin_t = update.t

        self._d2s = 0.
        self._dx = 0.
        self._dy = 0.

    def process(self, update: TouchpadUpdate) -> bool:
        """
        "Upgrade" three- to four-finger gesture and so on
        """
        if update.n_touches > self.n_touches:
            if update.t - self._begin_t < 0.2:
                return False

        """
        Gesture finished?
        """
        if update.n_touches == 0:
            return False

        if len(update.touches) == 0:
            return True

        dx = 0.
        dy = 0.
        d2s = 0.
        for i, x, y, z in update.touches:
            try:
                idx = [it[0] for it in self._touchpad_update.touches].index(i)

                dx += x - [it[1] for it in self._touchpad_update.touches][idx]
                d2s += (x - [it[1] for it in self._touchpad_update.touches][idx])**2

                dy += y - [it[2] for it in self._touchpad_update.touches][idx]
                d2s += (y - [it[2] for it in self._touchpad_update.touches][idx])**2
            except Exception:
                pass

        self._dx += dx / self.n_touches
        self._dy += dy / self.n_touches
        self._d2s += d2s / self.n_touches

        """
        Update
        """
        self.update({
            'delta_x': self._dx,
            'delta_y': self._dy,
            'delta2_s': self._d2s,
        })


        self._touchpad_update = update
        return True

    def __str__(self) -> str:
        return "HigherSwipe(%d)" % self.n_touches


class Gestures:
    def __init__(self, touchpad: Touchpad) -> None:
        self._listeners: list[Callable[[Gesture], None]] = []
        self._active_gesture: Optional[PyEvdevGesture] = None

        touchpad.listener(self.on_update)

    def listener(self, l: Callable[[Gesture], None]) -> None:
        self._listeners += [l]

    def reset(self) -> None:
        self._active_gesture = None

    def on_update(self, update: TouchpadUpdate) -> None:
        was_pending = True
        if self._active_gesture is not None:
            was_pending = self._active_gesture.pending

            if not self._active_gesture.process(update):
                self._active_gesture._terminate()
                self._active_gesture = None

        if self._active_gesture is None:
            if update.n_touches == 1:
                self._active_gesture = SingleFingerMoveGesture(self, update)
            elif update.n_touches == 2:
                self._active_gesture = TwoFingerSwipePinchGesture(self, update)
            elif update.n_touches > 2:
                self._active_gesture = HigherSwipeGesture(self, update)

        if self._active_gesture is not None:
            if was_pending and not self._active_gesture.pending:
                for l in self._listeners:
                    l(self._active_gesture)


class PyEvdevGestureProvider(GestureProvider, Thread):
    def __init__(self, gesture_listener: Callable[[Gesture], bool]) -> None:
        Thread.__init__(self)
        GestureProvider.__init__(self, gesture_listener)

        self._touchpads: list[tuple[Touchpad, Gestures]] = []
        self._running = True

        self._captured = False

    def on_pywm_gesture(self, kind: str, time_msec: int, args: list[Union[float, int]]) -> int:
        return 1 if len(self._touchpads) > 0 else 0

    def on_pywm_motion(self, time_msec: int, delta_x: float, delta_y: float) -> int:
        return 2 if self._captured else 0

    def on_pywm_axis(self, time_msec: int, source: int, orientation: int, delta: float, delta_discrete: int) -> int:
        return 2 if self._captured else 0

    def _gesture_listener(self, gesture: Gesture) -> None:
        if self._on_gesture(gesture):
            self._captured = True
            def finish_gesture() -> None:
                self._captured = False
            gesture.listener(GestureListener(None, finish_gesture))

    def _start_pad(self, name: str, path: str) -> None:
        touchpad = Touchpad(path)
        gestures = Gestures(touchpad)
        gestures.listener(self._gesture_listener)

        self._touchpads += [
            (touchpad, gestures)
        ]
        touchpad.start()
        logger.info("Started touchpad at %s", self._touchpads[-1][0].path)

    def _stop_pad(self, idx: int) -> None:
        self._touchpads[idx][0].stop()
        logger.info("Stopping touchpad at %s...", self._touchpads[idx][0].path)
        self._touchpads[idx][0].join()
        logger.info("...stopped")
        del self._touchpads[idx]

    def update(self) -> None:
        validated = [False for _ in self._touchpads]
        for name, path in find_all_touchpads():
            try:
                i = [t.path for t, g in self._touchpads].index(path)
                validated[i] = True
            except ValueError:
                logger.info("Found new touchpad: %s at %s", name, path)
                self._start_pad(name, path)

        for i, v in reversed(list(enumerate(validated))):
            if not v:
                logger.info("Touchpad at %s disappeared", self._touchpads[i][0].path)
                self._stop_pad(i)

    def stop(self) -> None:
        self._running = False

    def reset_gestures(self) -> None:
        for _, g in self._touchpads:
            g.reset()

    def run(self) -> None:
        try:
            while self._running:
                self.update()
                time.sleep(.5)
        finally:
            for i, _ in reversed(list(enumerate(self._touchpads))):
                self._stop_pad(i)

    def start(self) -> None:
        Thread.start(self)
