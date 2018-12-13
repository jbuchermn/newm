from pywm import PYWM_PRESSED

from pywm.touchpad import (
    SingleFingerMoveGesture,
    TwoFingerSwipePinchGesture,
    GestureListener,
    LowpassGesture
)
from .overlay import Overlay, ExitOverlayTransition


class PinchOverlay(Overlay):
    def __init__(self, layout):
        super().__init__(self)

        self.layout = layout
        self.state = self.layout.state.copy()

        self.x = self.state.i + .5 * self.state.size
        self.y = self.state.j + .5 * self.state.size
        self.size = self.state.size

        """
        Boundaries of movement
        """
        self.x_bounds = [self.state.min_i + .5 * self.state.size,
                         self.state.max_i + .5 * self.state.size]
        self.y_bounds = [self.state.min_j + .5 * self.state.size,
                         self.state.max_j + .5 * self.state.size]
        self.size_bounds = [1, 5]

        self.gesture_start_x = None
        self.gesture_start_y = None
        self.gesture_start_size = None

        self._set_state()

    def _exit_finished(self):
        self.layout.rescale()
        self.layout.update_cursor()
        super()._exit_finished()

    def _exit_transition(self):
        self.layout.state = self.state
        return ExitOverlayTransition(
            self, .2,
            size=round(self.size),
            i=round(self.x - .5*self.size),
            j=round(self.y - .5*self.size))

    def _set_state(self):
        self.x = max(self.x, self.x_bounds[0])
        self.x = min(self.x, self.x_bounds[1])
        self.y = max(self.y, self.y_bounds[0])
        self.y = min(self.y, self.y_bounds[1])
        self.size = max(self.size, self.size_bounds[0])
        self.size = min(self.size, self.size_bounds[1])

        new_state = self.state.copy()
        new_state.i = self.x - .5 * self.size
        new_state.j = self.y - .5 * self.size
        new_state.size = self.size

        self.state = new_state

    def on_gesture(self, gesture):
        if isinstance(gesture, TwoFingerSwipePinchGesture):
            self.gesture_start_x = self.x
            self.gesture_start_y = self.y
            self.gesture_start_size = self.size
            LowpassGesture(gesture).listener(GestureListener(
                self._on_two_finger,
                lambda: self._on_two_finger(None)
            ))
            return True
        elif isinstance(gesture, SingleFingerMoveGesture):
            self.gesture_start_x = self.x
            self.gesture_start_y = self.y
            self.gesture_start_size = self.size
            LowpassGesture(gesture).listener(GestureListener(
                self._on_single_finger,
                lambda: self._on_single_finger(None)
            ))
            return True

        return False

    def _on_two_finger(self, values):
        if values is None:
            self.gesture_start_x = None
            if not self.layout.modifiers & self.layout.mod:
                self.layout.exit_overlay()
        else:
            self.x = self.gesture_start_x - 4*values['delta_x']
            self.y = self.gesture_start_y - 4*values['delta_y']
            self.size = self.gesture_start_size / values['scale']

            self._set_state()
            self.layout.state = self.state
            self.layout.update()

    def _on_single_finger(self, values):
        if values is None:
            self.gesture_start_x = None
            if not self.layout.modifiers & self.layout.mod:
                self.layout.exit_overlay()
        else:
            self.x = self.gesture_start_x - 4*values['delta_x']
            self.y = self.gesture_start_y - 4*values['delta_y']

            self._set_state()
            self.layout.state = self.state
            self.layout.update()

    def on_motion(self, time_msec, delta_x, delta_y):
        return False

    def on_axis(self, time_msec, source, orientation, delta, delta_discrete):
        return False

    def on_key(self, time_msec, keycode, state, keysyms):
        print(state, keysyms)
        if state != PYWM_PRESSED and self.layout.mod_sym in keysyms \
                and self.gesture_start_x is None:
            self.layout.exit_overlay()

