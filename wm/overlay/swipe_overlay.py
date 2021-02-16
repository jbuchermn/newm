from pywm.touchpad import GestureListener, LowpassGesture
from .overlay import Overlay

_momentum_factor = 50.
_locked_dist = 0.05


class SwipeOverlay(Overlay):
    def __init__(self, layout):
        super().__init__(self)

        self.layout = layout

        self.x = self.layout.state.i + .5 * self.layout.state.size
        self.y = self.layout.state.j + .5 * self.layout.state.size
        self.size = self.layout.state.size

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
        min_i, min_j, max_i, max_j = self.extent = self.layout.state.get_extent(strict=True)

        min_i += .5*self.size - self.size + 1
        min_j += .5*self.size - self.size + 1
        max_i += .5*self.size
        max_j += .5*self.size

        def x_bound(x):
            if x < min_i:
                return min_i - .3 * (1 - 1/(1 + (min_i - x)))
            elif x < max_i:
                return x
            else:
                return max_i + .3 * (1 - 1/(1 + (x - max_i)))


        self.x_bound = x_bound

        def y_bound(y):
            if y < min_j:
                return min_i - .3 * (1 - 1/(1 + (min_j - y)))
            elif y < max_j:
                return y
            else:
                return max_j + .3 * (1 - 1/(1 + (y - max_j)))
        self.y_bound = y_bound

        self._set_state()

    def _exit_finished(self):
        self.layout.update_cursor()
        super()._exit_finished()

    def _exit_transition(self):
        i = self.x - .5*self.layout.state.size
        j = self.y - .5*self.layout.state.size

        if self.locked_x:
            i -= max(-.5, min(.5, self.momentum_x * _momentum_factor))
        else:
            j -= max(-.5, min(.5, self.momentum_y * _momentum_factor))

        i = max(i, self.extent[0] - self.size + 1)
        j = max(j, self.extent[1] - self.size + 1)
        i = min(i, self.extent[2])
        j = min(j, self.extent[3])

        fi = round(i)
        fj = round(j)

        dt = .6 * (abs(i - fi) + abs(j-fj))
        return self.layout.state.copy(i=fi, j=fj), dt

    def _set_state(self):
        self.x = self.x_bound(self.x)
        self.y = self.y_bound(self.y)

        self.layout.state.i = self.x - .5 * self.size
        self.layout.state.j = self.y - .5 * self.size
        self.layout.damage()


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

    def on_motion(self, time_msec, delta_x, delta_y):
        return False

    def on_axis(self, time_msec, source, orientation, delta, delta_discrete):
        return False

