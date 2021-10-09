from __future__ import annotations
from typing import TYPE_CHECKING

import logging

from pywm import PYWM_PRESSED
from pywm.touchpad import (
    SingleFingerMoveGesture,
    TwoFingerSwipePinchGesture,
    GestureListener,
    LowpassGesture
)
from pywm.touchpad.gestures import Gesture

from .overlay import Overlay

if TYPE_CHECKING:
    from ..layout import Layout
    from ..view import View

logger = logging.getLogger(__name__)

class MoveResizeFloatingOverlay(Overlay):
    def __init__(self, layout: Layout, view: View):
        super().__init__(layout)

        self.layout.update_cursor(False)

        self.view = view
        self.i = 0.
        self.j = 0.
        self.w = 1.
        self.h = 1.

        self.min_w, self.min_h = view.find_min_w_h()
        try:
            state = self.layout.state.get_view_state(self.view)
            self.i = state.i
            self.j = state.j
            self.w = state.w
            self.h = state.h
        except Exception:
            logger.warn("Unexpected: Could not access view %s state", self.view)

        self._motion_mode = True
        self._gesture_mode = False
        self._gesture_last_dx = 0.
        self._gesture_last_dy = 0.

    def move(self, dx: float, dy: float) -> None:
        self.i += dx * self.layout.state.size
        self.j += dy * self.layout.state.size

        self.layout.state.update_view_state(self.view, i=self.i, j=self.j)
        self.layout.damage()

    def resize(self, dx: float, dy: float) -> None:
        self.w += dx * self.layout.state.size
        self.h += dy * self.layout.state.size

        self.w = max(self.min_w, self.w)
        self.h = max(self.min_h, self.h)

        self.layout.state.update_view_state(self.view, w=self.w, h=self.h)
        self.layout.damage()

    def gesture_move(self, values: dict[str, float]) -> None:
        if self._gesture_mode:
            self.move(
                values['delta_x'] - self._gesture_last_dx,
                values['delta_y'] - self._gesture_last_dy)
            self._gesture_last_dx = values['delta_x']
            self._gesture_last_dy = values['delta_y']

    def gesture_resize(self, values: dict[str, float]) -> None:
        if self._gesture_mode:
            self.resize(
                values['delta_x'] - self._gesture_last_dx,
                values['delta_y'] - self._gesture_last_dy)
            self._gesture_last_dx = values['delta_x']
            self._gesture_last_dy = values['delta_y']

    def gesture_finish(self) -> None:
        self._gesture_mode = False
        self._gesture_last_dx = 0
        self._gesture_last_dy = 0

        if not self.layout.modifiers & self.layout.mod:
            logger.debug("MoveResizeFloatingOverlay: Exiting on gesture end")
            self.layout.exit_overlay()


    def on_motion(self, time_msec: int, delta_x: float, delta_y: float) -> bool:
        if self._motion_mode:
            self.move(delta_x, delta_y);
        return False

    def on_button(self, time_msec: int, button: int, state: int) -> bool:
        if self._motion_mode:
            logger.debug("MoveFloatingOverlay: Exiting on mouse release")
            self.layout.exit_overlay()
            return True
        return False

    def on_gesture(self, gesture: Gesture) -> bool:
        if isinstance(gesture, TwoFingerSwipePinchGesture):
            logger.debug("MoveResizeFloatingOverlay: New TwoFingerSwipePinch")

            self._motion_mode = False
            self._gesture_mode = True
            LowpassGesture(gesture).listener(GestureListener(
                self.gesture_resize,
                self.gesture_finish
            ))
            return True

        if isinstance(gesture, SingleFingerMoveGesture):
            logger.debug("MoveResizeFloatingOverlay: New SingleFingerMove")

            self._motion_mode = False
            self._gesture_mode = True
            LowpassGesture(gesture).listener(GestureListener(
                self.gesture_move,
                self.gesture_finish
            ))
            return True

        return False


    def on_key(self, time_msec: int, keycode: int, state: int, keysyms: str) -> bool:
        if state != PYWM_PRESSED and self.layout.mod_sym in keysyms:
            if self._gesture_mode == False and self._motion_mode == False:
                logger.debug("MoveResizeFlaotingOverlay: Exiting on mod release")
                self.layout.exit_overlay()
                return True
        return False

    def pre_destroy(self) -> None:
        self.layout.update_cursor(True)
