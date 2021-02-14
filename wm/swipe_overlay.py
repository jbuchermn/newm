from pywm.touchpad import GestureListener, LowpassGesture
from .overlay import Overlay

_momentum_factor = 50.
_locked_dist = 0.05


class SwipeOverlay(Overlay):
    def __init__(self, layout):
        super().__init__(self)

        self.layout = layout
        self.state = self.layout.state.copy()

        self.x = self.state.i + .5 * self.state.size
        self.y = self.state.j + .5 * self.state.size
        self.size = self.state.size

        self.initial_x = self.x
        self.initial_y = self.y
        self.locked_x = None

        # """
        # Only allow x scrolling
        # """
        # self.locked_x = True

        """
        Current state
        """
        self.last_delta_x = 0
        self.last_delta_y = 0
        self.momentum_x = 0
        self.momentum_y = 0

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
        new_state = self.state.copy()

        new_state.i = self.x - .5*self.state.size
        new_state.j = self.y - .5*self.state.size

        if self.locked_x:
            new_state.i -= max(-.5, min(.5, self.momentum_x * _momentum_factor))
        else:
            new_state.j -= max(-.5, min(.5, self.momentum_y * _momentum_factor))

        new_state.i = round(new_state.i)
        new_state.j = round(new_state.j)
        return new_state

    def _set_state(self):
        self.x = max(self.x, self.x_bounds[0])
        self.x = min(self.x, self.x_bounds[1])
        self.y = max(self.y, self.y_bounds[0])
        self.y = min(self.y, self.y_bounds[1])

        new_state = self.state.copy()
        new_state.i = self.x - .5 * self.size
        new_state.j = self.y - .5 * self.size

        self.state = new_state

    def on_gesture(self, gesture):
        LowpassGesture(gesture).listener(GestureListener(
            self._on_update,
            lambda: self.layout.exit_overlay()
        ))

    def _on_update(self, values):
        if self.locked_x is None:
            if values['delta_x']**2 + values['delta_y']**2 > _locked_dist**2:
                self.locked_x = abs(values['delta_x']) \
                    > abs(values['delta_y'])

                if self.locked_x:
                    self.initial_x += 3 * self.size * values['delta_x']
                else:
                    self.initial_y += 3 * self.size * values['delta_y']

        if self.locked_x is not None:
            if self.locked_x:
                self.x = self.initial_x - 3 * self.size * values['delta_x']
            else:
                self.y = self.initial_y - 3 * self.size * values['delta_y']

        self.momentum_x = values['delta_x'] - self.last_delta_x
        self.momentum_y = values['delta_y'] - self.last_delta_y
        self.last_delta_x = values['delta_x']
        self.last_delta_y = values['delta_y']

        self._set_state()
        self.layout.state = self.state
        self.layout.damage()

    def on_motion(self, time_msec, delta_x, delta_y):
        return False

    def on_axis(self, time_msec, source, orientation, delta, delta_discrete):
        return False

