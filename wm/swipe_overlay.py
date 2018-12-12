from .overlay import Overlay, ExitOverlayTransition


class SwipeOverlay(Overlay):
    def __init__(self, layout):
        super().__init__(self)

        self.layout = layout
        self.state = self.layout.state.copy()

        self.x = self.state.i + .5 * self.state.size
        self.y = self.state.j + .5 * self.state.size

        self.initial_x = self.x
        self.initial_y = self.y

        """
        Boundaries of movement
        """
        self.x_bounds = [self.state.min_i + .5 * self.state.size,
                         self.state.max_i + .5 * self.state.size]
        self.y_bounds = [self.state.min_j + .5 * self.state.size,
                         self.state.max_j + .5 * self.state.size]

        self._set_state()

    def _exit_finished(self):
        self.layout.update_cursor()
        super()._exit_finished()

    def _exit_transition(self):
        self.layout.state = self.state
        return ExitOverlayTransition(
            self, .2,
            i=round(self.x - .5*self.state.size),
            j=round(self.y - .5*self.state.size))

    def _set_state(self):
        self.x = max(self.x, self.x_bounds[0])
        self.x = min(self.x, self.x_bounds[1])
        self.y = max(self.y, self.y_bounds[0])
        self.y = min(self.y, self.y_bounds[1])

        new_state = self.state.copy()
        new_state.i = self.x - .5 * self.state.size
        new_state.j = self.y - .5 * self.state.size

        self.state = new_state

    def on_gesture(self, gesture):
        gesture.lp_listener(self.on_gesture_update)

    def on_gesture_update(self, values):
        if values is None:
            self.layout.exit_overlay()
        else:
            self.x = self.initial_x - 4*values['delta_x']

            """
            Only scroll in x direction for now
            """
            # self.y = self.initial_y - 4*values['delta_y']

            self._set_state()
            self.layout.state = self.state
            self.layout.update()

    def on_motion(self, time_msec, delta_x, delta_y):
        return False

    def on_axis(self, time_msec, source, orientation, delta, delta_discrete):
        return False

