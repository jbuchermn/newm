from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from ..gestures import Gesture, GestureListener, LowpassGesture
from .overlay import Overlay
from ..grid import Grid
from ..config import configured_value

if TYPE_CHECKING:
    from ..layout import Layout
    from ..state import LayoutState

conf_lock_dist = configured_value('swipe.lock_dist', 0.01)
conf_gesture_factor = configured_value('swipe.gesture_factor', 4)
conf_grid_ovr = configured_value('swipe.grid_ovr', 0.2)
conf_grid_m = configured_value('swipe.grid_m', 1)

conf_grid_min_dist = configured_value('grid.min_dist', .05)

conf_lp_freq = configured_value('gestures.lp_freq', 60.)
conf_lp_inertia = configured_value('gestures.lp_inertia', .8)

conf_gesture_binding_swipe = configured_value('gesture_bindings.swipe', (None, 'swipe-3'))

class SwipeOverlay(Overlay):
    def __init__(self, layout: Layout) -> None:
        super().__init__(layout)

        self.layout = layout
        self.workspace = layout.get_active_workspace()
        self.ws_state = layout.state.get_workspace_state(self.workspace)

        self.size = self.ws_state.size
        self.i = self.ws_state.i
        self.j = self.ws_state.j

        self.locked_x: Optional[bool] = None

        # """
        # Only allow x scrolling
        # """
        # self.locked_x = True

        self.initial_x = self.i
        self.initial_y = self.j
        self.last_delta_x = 0.
        self.last_delta_y = 0.

        """
        Grids
        """
        min_i, min_j, max_i, max_j = self.extent = [round(r) for r in self.ws_state.get_extent()]

        max_i -= round(self.size) - 1
        max_j -= round(self.size) - 1

        self._invalid = [False, False]
        if max_i < min_i:
            self._invalid[0] = True

        if max_j < min_j:
            self._invalid[1] = True

        self.i_grid = Grid("i", min_i, max_i, self.i, conf_grid_ovr(), conf_grid_m())
        self.j_grid = Grid("j", min_j, max_j, self.j, conf_grid_ovr(), conf_grid_m())

        self._has_gesture = False

        self._set_state()

    def _exit_finished(self) -> None:
        self.layout.update_cursor()
        super()._exit_finished()

    def _exit_transition(self) -> tuple[Optional[LayoutState], Optional[float]]:
        i, ti = self.i_grid.final(throw_dist_max=self.size - conf_grid_min_dist())
        j, tj = self.j_grid.final(throw_dist_max=self.size - conf_grid_min_dist())
        t = None

        if self.locked_x is not None:
            if self.locked_x:
                j = round(self.initial_y)
                t = ti
            else:
                i = round(self.initial_x)
                t = tj

        return self.layout.state.replacing_workspace_state(self.workspace, i=i, j=j), t

    def _set_state(self) -> None:
        if not self._invalid[0]:
            self.ws_state.i = self.i_grid.at(self.i)
        if not self._invalid[1]:
            self.ws_state.j = self.j_grid.at(self.j)
        self.layout.damage()


    def on_gesture(self, gesture: Gesture) -> bool:
        if gesture.kind != conf_gesture_binding_swipe()[1]:
            self.layout.exit_overlay()
            return False

        if not self._has_gesture:
            LowpassGesture(gesture, conf_lp_inertia(), conf_lp_freq()).listener(GestureListener(
                self._on_update,
                lambda: self.layout.exit_overlay()
            ))
            self._has_gesture = True
        return True

    def _on_update(self, values: dict[str, float]) -> None:
        if self.locked_x is None:
            if values['delta_x']**2 + values['delta_y']**2 > conf_lock_dist()**2:
                self.locked_x = abs(values['delta_x']) \
                    > abs(values['delta_y'])

                if self.locked_x:
                    self.initial_x += conf_gesture_factor() * self.size * values['delta_x']
                else:
                    self.initial_y += conf_gesture_factor() * self.size * values['delta_y']

        if self.locked_x is not None:
            if self.locked_x:
                self.i = self.initial_x - conf_gesture_factor() * self.size * values['delta_x']
            else:
                self.j = self.initial_y - conf_gesture_factor() * self.size * values['delta_y']

        self.last_delta_x = values['delta_x']
        self.last_delta_y = values['delta_y']

        self._set_state()

    def on_motion(self, time_msec: int, delta_x: float, delta_y: float) -> bool:
        return False

    def on_axis(self, time_msec: int, source: int, orientation: int, delta: float, delta_discrete: int) -> bool:
        return False

