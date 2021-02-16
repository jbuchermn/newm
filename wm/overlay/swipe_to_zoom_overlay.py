from pywm.touchpad import GestureListener, LowpassGesture
from .overlay import Overlay

_momentum_factor = 50.

class SwipeToZoomOverlay(Overlay):
    def __init__(self, layout):
        super().__init__(self)

        self.layout = layout

        self.size = self.layout.state.size

        """
        Four-finger mode
        """
        self.initial_size = self.size

        """
        Boundaries of movement
        """
        
        def size_bound(s):
            if s < 1:
                return 1 - .3 * (1 - 1/(1 + (1 - s)))
            elif s < self.initial_size + 1:
                return s
            else:
                return self.initial_size + 1 + .3 * (1 - 1/(1 + (s - (self.initial_size + 1))))

        self.size_bound = size_bound

        """
        Current state
        """
        self.last_delta_y = 0
        self.momentum_y = 0

        self._set_state()

    def _exit_finished(self):
        self.layout.update_cursor()
        super()._exit_finished()

    def _exit_transition(self):
        size = self.size
        size -= max(-.5, min(.5, self.momentum_y * _momentum_factor))

        size = self.size_bound(size)

        fsize = round(size)
        scale = fsize
        dt = .6 * abs(size - fsize)
        return self.layout.state.copy(size=fsize, scale=scale), dt

    def _set_state(self):
        self.size = self.size_bound(self.size)

        self.layout.state.size = self.size
        self.layout.damage()

    def on_gesture(self, gesture):
        LowpassGesture(gesture).listener(GestureListener(
            self._on_update,
            lambda: self.layout.exit_overlay()
        ))

    def _on_update(self, values):
        self.size = self.initial_size - 4*values['delta_y']

        self.momentum_y = values['delta_y'] - self.last_delta_y
        self.last_delta_y = values['delta_y']

        self._set_state()

    def on_motion(self, time_msec, delta_x, delta_y):
        return False

    def on_axis(self, time_msec, source, orientation, delta, delta_discrete):
        return False

