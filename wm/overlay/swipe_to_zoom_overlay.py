from pywm.touchpad import GestureListener, LowpassGesture
from .overlay import Overlay
from ..grid import Grid

GRID_OVR = 0.3
GRID_M = 2


class SwipeToZoomOverlay(Overlay):
    def __init__(self, layout):
        super().__init__(self)

        self.layout = layout

        self.size = self.layout.state.size

        self.initial_size = self.size
        self.last_delta_y = 0

        """
        Grid
        """
        self.grid = Grid(1, self.initial_size + 1, self.initial_size, GRID_OVR, GRID_M)
        

        self._set_state()

    def _exit_finished(self):
        self.layout.update_cursor()
        super()._exit_finished()

    def _exit_transition(self):
        size, t = self.grid.final()
        scale = size
        return self.layout.state.copy(size=size, scale=scale), t

    def _set_state(self):
        self.layout.state.size = self.grid.at(self.size)
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

