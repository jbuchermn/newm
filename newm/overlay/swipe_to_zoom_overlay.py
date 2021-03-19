from pywm.touchpad import GestureListener, LowpassGesture
from .overlay import Overlay
from ..grid import Grid
from ..hysteresis import Hysteresis
from ..config import configured_value

conf_grid_ovr = configured_value("swipe_zoom.ovr", 0.3)
conf_grid_m = configured_value("swipe_zoom.m", 1)
conf_hyst = configured_value("swipe_zoom.hyst", 0.2)


class SwipeToZoomOverlay(Overlay):
    def __init__(self, layout):
        super().__init__(self)

        self.layout = layout
        self._focused = self.layout.find_focused_view()
        self._focused_br = None
        if self._focused is not None:
            state = self.layout.state.get_view_state(self._focused)
            self._focused_br = state.i + state.w, state.j + state.h

        self.i = self.layout.state.i
        self.j = self.layout.state.j
        self.size = self.layout.state.size
        self.initial_size = self.size

        self.initial_scale = self.layout.state.scale
        self.last_delta_y = 0

        """
        Grid
        """
        self.grid = Grid("size", 1, self.initial_size + 1, self.initial_size, conf_grid_ovr(), conf_grid_m())
        self.hyst = Hysteresis(conf_hyst(), self.size)
        

        self._set_state()

        self._has_gesture = False

    def _exit_finished(self):
        self.layout.update_cursor()
        super()._exit_finished()

    def _exit_transition(self):
        size, t = self.grid.final()
        if self._focused is None:
            return self.layout.state.copy(size=size, scale=self.initial_scale), t
        else:
            return self.layout.state.copy(size=size, scale=self.initial_scale).focusing_view(self._focused), t

    def _set_state(self):
        self.layout.state.size = self.grid.at(self.size)
        self.layout.state.scale = float(self.hyst(self.layout.state.size)) / self.layout.state.size

        # Enforce constraints real-time
        if self._focused_br is not None:
            # Move bottom right corner into view
            i, j = self._focused_br
            self.layout.state.i = max(self.i, i - self.layout.state.size)
            self.layout.state.j = max(self.j, j - self.layout.state.size)
        self.layout.state.constrain()

        self.layout.damage()

    def on_gesture(self, gesture):
        if not self._has_gesture:
            LowpassGesture(gesture).listener(GestureListener(
                self._on_update,
                lambda: self.layout.exit_overlay()
            ))
            self._has_gesture = True

    def _on_update(self, values):
        self.size = self.initial_size - 4*values['delta_y']

        self.momentum_y = values['delta_y'] - self.last_delta_y
        self.last_delta_y = values['delta_y']

        self._set_state()

    def on_motion(self, time_msec, delta_x, delta_y):
        return False

    def on_axis(self, time_msec, source, orientation, delta, delta_discrete):
        return False

