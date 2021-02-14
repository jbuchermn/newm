from pywm.touchpad import GestureListener, LowpassGesture
from .overlay import Overlay

_momentum_factor = 50.

class SwipeToZoomOverlay(Overlay):
    def __init__(self, layout):
        super().__init__(self)

        self.layout = layout
        self.state = self.layout.state.copy()

        self.size = self.state.size

        """
        Four-finger mode
        """
        self.initial_size = self.size

        """
        Boundaries of movement
        """
        self.size_bounds = [1, 5]

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
        new_state = self.state.copy()

        size = self.size
        size -= max(-.5, min(.5, self.momentum_y * _momentum_factor))

        size = max(size, self.size_bounds[0])
        size = min(size, self.size_bounds[1])

        new_state.size = round(size)
        new_state.scale = self.layout.get_scale(new_state)
        return new_state

    def _set_state(self):
        self.size = max(self.size, self.size_bounds[0])
        self.size = min(self.size, self.size_bounds[1])

        new_state = self.state.copy()
        new_state.size = self.size

        self.state = new_state

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
        self.layout.state = self.state
        self.layout.damage()

    def on_motion(self, time_msec, delta_x, delta_y):
        return False

    def on_axis(self, time_msec, source, orientation, delta, delta_discrete):
        return False

