import logging

from pywm import PYWM_PRESSED

from pywm.touchpad import (
    SingleFingerMoveGesture,
    TwoFingerSwipePinchGesture,
    GestureListener,
    LowpassGesture
)

from .overlay import Overlay

class MoveResizeFloatingOverlay(Overlay):
    def __init__(self, layout, view):
        super().__init__(layout)

        self.view = view
        self.i = 0
        self.j = 0
        self.w = 1
        self.h = 1

        self.min_w, self.min_h = view.find_min_w_h()
        try:
            state = self.layout.state.get_view_state(self.view)
            self.i = state.i
            self.j = state.j
            self.w = state.w
            self.h = state.h
        except Exception:
            logging.warn("Unexpected: Could not access view %s state", self.view)

        self._motion_mode = True
        self._gesture_mode = False
        self._gesture_last_dx = 0
        self._gesture_last_dy = 0

    def move(self, dx, dy):
        self.i += dx * self.layout.state.scale
        self.j += dy * self.layout.state.scale

        self.layout.state.update_view_state(self.view, i=self.i, j=self.j)
        self.layout.damage()

    def resize(self, dx, dy):
        self.w += dx * self.layout.state.scale
        self.h += dy * self.layout.state.scale

        self.w = max(self.min_w, self.w)
        self.h = max(self.min_h, self.h)

        self.layout.state.update_view_state(self.view, w=self.w, h=self.h)
        self.layout.damage()

    def gesture_move(self, values):
        if self._gesture_mode:
            self.move(
                values['delta_x'] - self._gesture_last_dx,
                values['delta_y'] - self._gesture_last_dy)
            self._gesture_last_dx = values['delta_x']
            self._gesture_last_dy = values['delta_y']

    def gesture_resize(self, values):
        if self._gesture_mode:
            self.resize(
                values['delta_x'] - self._gesture_last_dx,
                values['delta_y'] - self._gesture_last_dy)
            self._gesture_last_dx = values['delta_x']
            self._gesture_last_dy = values['delta_y']

    def gesture_finish(self):
        self._gesture_mode = False
        self._gesture_last_dx = 0
        self._gesture_last_dy = 0

        if not self.layout.modifiers & self.layout.mod:
            logging.debug("MoveResizeFloatingOverlay: Exiting on gesture end")
            self.layout.exit_overlay()


    def on_motion(self, time_msec, delta_x, delta_y):
        if self._motion_mode:
            self.move(delta_x, delta_y);
        return False

    def on_button(self, time_msec, button, state):
        if self._motion_mode:
            logging.debug("MoveFloatingOverlay: Exiting on mouse release")
            self.layout.exit_overlay()
            return True
        return False

    def on_gesture(self, gesture):
        if isinstance(gesture, TwoFingerSwipePinchGesture):
            logging.debug("MoveResizeFloatingOverlay: New TwoFingerSwipePinch")

            self._motion_mode = False
            self._gesture_mode = True
            LowpassGesture(gesture).listener(GestureListener(
                self.gesture_resize,
                self.gesture_finish
            ))
            return True

        if isinstance(gesture, SingleFingerMoveGesture):
            logging.debug("MoveResizeFloatingOverlay: New SingleFingerMove")

            self._motion_mode = False
            self._gesture_mode = True
            LowpassGesture(gesture).listener(GestureListener(
                self.gesture_move,
                self.gesture_finish
            ))
            return True


    def on_key(self, time_msec, keycode, state, keysyms):
        if state != PYWM_PRESSED and self.layout.mod_sym in keysyms:
            if self._gesture_mode == False and self._motion_mode == False:
                logging.debug("MoveResizeFlaotingOverlay: Exiting on mod release")
                self.layout.exit_overlay()
