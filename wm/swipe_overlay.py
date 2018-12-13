from pywm.touchpad import GestureListener, HigherSwipeGesture, LowpassGesture
from .overlay import Overlay, ExitOverlayTransition


class SwipeOverlay(Overlay):
    def __init__(self, layout):
        super().__init__(self)

        self.layout = layout
        self.state = self.layout.state.copy()

        self.x = self.state.i + .5 * self.state.size
        self.y = self.state.j + .5 * self.state.size
        self.size = self.state.size

        """
        Three-Finger mode
        """
        self.initial_x = self.x
        self.initial_y = self.y
        self.locked_x = None

        """
        Four-finger mode
        """
        self.initial_size = self.size

        """
        Boundaries of movement
        """
        self.x_bounds = [self.state.min_i + .5 * self.state.size,
                         self.state.max_i + .5 * self.state.size]
        self.y_bounds = [self.state.min_j + .5 * self.state.size,
                         self.state.max_j + .5 * self.state.size]
        self.size_bounds = [1, 5]

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
            i=round(self.x - .5*self.state.size),
            j=round(self.y - .5*self.state.size))

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
        if not isinstance(gesture, HigherSwipeGesture):
            self.layout.exit_overlay()
            return

        if gesture.n_touches == 3:
            LowpassGesture(gesture).listener(GestureListener(
                self._on_swipe_update,
                lambda: self.layout.exit_overlay()
            ))
        elif gesture.n_touches == 4:
            LowpassGesture(gesture).listener(GestureListener(
                self._on_zoom_update,
                lambda: self.layout.exit_overlay()
            ))

    def _on_swipe_update(self, values):
        if self.locked_x is None:
            if values['delta_x']**2 + values['delta_y']**2 > 0.005:
                self.locked_x = abs(values['delta_x']) \
                    > abs(values['delta_y'])

                if self.locked_x:
                    self.initial_x += 4*values['delta_x']
                else:
                    self.initial_y += 4*values['delta_y']

        if self.locked_x is not None:
            if self.locked_x:
                self.x = self.initial_x - 4*values['delta_x']
            else:
                self.y = self.initial_y - 4*values['delta_y']

        self._set_state()
        self.layout.state = self.state
        self.layout.update()

    def _on_zoom_update(self, values):
        self.size = self.initial_size - 4*values['delta_y']

        self._set_state()
        self.layout.state = self.state
        self.layout.update()

    def on_motion(self, time_msec, delta_x, delta_y):
        return False

    def on_axis(self, time_msec, source, orientation, delta, delta_discrete):
        return False

