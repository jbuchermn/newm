from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from pywm.touchpad import GestureListener, LowpassGesture
from pywm.touchpad.gestures import Gesture
from .overlay import Overlay
from ..grid import Grid
from ..hysteresis import Hysteresis
from ..config import configured_value

if TYPE_CHECKING:
    from ..layout import Layout
    from ..state import LayoutState

conf_grid_ovr = configured_value("swipe_zoom.grid_ovr", 0.2)
conf_grid_m = configured_value("swipe_zoom.grid_m", 1)
conf_hyst = configured_value("swipe_zoom.hyst", 0.2)
conf_gesture_factor = configured_value("swipe_zoom.gesture_factor", 4)


class SwipeToZoomOverlay(Overlay):
    def __init__(self, layout: Layout) -> None:
        super().__init__(layout)

        self.layout = layout

        self.i = self.layout.state.i
        self.j = self.layout.state.j
        self.size = self.layout.state.size
        self.initial_size = round(self.size)

        self.last_delta_y = 0.

        self._focused = self.layout.find_focused_view()
        self._focused_br = None
        min_size = 1
        if self._focused is not None:
            state = self.layout.state.get_view_state(self._focused)
            min_size = min(self.initial_size, round(max(state.w, state.h)))
            if self.i + self.size > state.i + state.w - 0.1 and self.j + self.size > state.j + state.h - 0.1:
                self._focused_br = state.i + state.w, state.j + state.h

        """
        Grid
        """
        self.grid = Grid("size", min_size, self.initial_size + 1, self.initial_size, conf_grid_ovr(), conf_grid_m())
        self.hyst = Hysteresis(conf_hyst(), self.size)
        

        self._set_state()

        self._has_gesture = False

    def _exit_finished(self) -> None:
        self.layout.update_cursor()
        super()._exit_finished()

    def _exit_transition(self) -> tuple[Optional[LayoutState], Optional[float]]:
        size, t = self.grid.final()
        state = self.layout.state.copy(size=size, size_origin=None)
        if self._focused is not None:
            state = state.focusing_view(self._focused)

        if size != self.initial_size:
            state = state.without_fullscreen(drop=True)

        return state, t

    def _set_state(self) -> None:
        self.layout.state.size_origin = float(self.hyst(self.layout.state.size))
        self.layout.state.size = self.grid.at(self.size)

        # Enforce constraints real-time
        if self._focused_br is not None:
            # Move bottom right corner into view
            i, j = self._focused_br
            self.layout.state.i = max(self.i, i - self.layout.state.size)
            self.layout.state.j = max(self.j, j - self.layout.state.size)
        self.layout.state.constrain()

        self.layout.damage()

    def on_gesture(self, gesture: Gesture) -> bool:
        if not self._has_gesture:
            LowpassGesture(gesture).listener(GestureListener(
                self._on_update,
                lambda: self.layout.exit_overlay()
            ))
            self._has_gesture = True

        return True

    def _on_update(self, values: dict[str, float]) -> None:
        self.size = self.initial_size - conf_gesture_factor()*values['delta_y']

        self.momentum_y = values['delta_y'] - self.last_delta_y
        self.last_delta_y = values['delta_y']

        self._set_state()

    def on_motion(self, time_msec: int, delta_x: float, delta_y: float) -> bool:
        return False

    def on_axis(self, time_msec: int, source: int, orientation: int, delta: float, delta_discrete: int) -> bool:
        return False

