from pywm import PYWM_PRESSED

from pywm.touchpad import (
    SingleFingerMoveGesture,
    TwoFingerSwipePinchGesture,
    GestureListener,
    LowpassGesture
)
from .overlay import Overlay


class MoveResizeOverlay(Overlay):
    def __init__(self, layout):
        super().__init__(self)

        self.layout = layout

        self.view = self.layout.find_focused_view()
        self.view_state = None
        self.w = 0
        self.h = 0

        self.gesture_started = False
        self.gesture_dx = 0
        self.gesture_dy = 0
        self._reset()

    def _reset(self):
        self.layout.damage()
        if self.view is not None:
            self.view_state = self.layout.state.get_view_state(self.view._handle)
            self.w = self.view_state.w
            self.h = self.view_state.h

    def on_gesture(self, gesture):
        if isinstance(gesture, TwoFingerSwipePinchGesture):
            self.gesture_dx = 0
            self.gesture_dy = 0
            self.gesture_started = True
            LowpassGesture(gesture).listener(GestureListener(
                self._on_two_finger,
                lambda: self._on_two_finger(None)
            ))

            return True
        elif isinstance(gesture, SingleFingerMoveGesture):
            self.gesture_dx = 0
            self.gesture_dy = 0
            self.gesture_started = True
            LowpassGesture(gesture).listener(GestureListener(
                self._on_single_finger,
                lambda: self._on_single_finger(None)
            ))
            return True

        return False

    def _on_two_finger(self, values):
        if self.view is None:
            return

        if values is None:
            self.gesture_started = False
            if not self.layout.modifiers & self.layout.mod:
                self.layout.exit_overlay()

        else:
            w, h = self.w, self.h
            if values['delta_x'] - self.gesture_dx > 0.1:
                w += 1
            elif values['delta_x'] - self.gesture_dx < -0.1:
                w = max(1, w - 1)
            elif values['delta_y'] - self.gesture_dy > 0.1:
                h += 1 
            elif values['delta_y'] - self.gesture_dy < -0.1:
                h = max(1, h - 1)
            else:
                return

            if (w, h) != (self.view_state.w, self.view_state.h):
                self.gesture_dx = values['delta_x']
                self.gesture_dy = values['delta_y']

                self.layout.animate_to(
                    self.layout.state.replacing_view_state(self.view._handle, w=w, h=h),
                    .3, self._reset)

    def _on_single_finger(self, values):
        if self.view is None:
            return

        if values is None:
            if not self.layout.modifiers & self.layout.mod:
                self.layout.exit_overlay()

            self.gesture_started = False
        else:
            pass

    def on_motion(self, time_msec, delta_x, delta_y):
        return False

    def on_axis(self, time_msec, source, orientation, delta, delta_discrete):
        return False

    def on_key(self, time_msec, keycode, state, keysyms):
        if state != PYWM_PRESSED and self.layout.mod_sym in keysyms \
                and not self.gesture_started:
            self.layout.exit_overlay()
