from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from pywm import PYWM_PRESSED

from .overlay import Overlay
from ..config import configured_value

if TYPE_CHECKING:
    from ..layout import Layout
    from ..state import LayoutState

conf_anim_t = configured_value("anim_time", .3)

class OverviewOverlay(Overlay):
    def __init__(self, layout: Layout):
        super().__init__(layout)
        self._original_state: Optional[LayoutState] = None

    def _enter_transition(self) -> tuple[LayoutState, float]:
        self._original_state = self.layout.state

        min_i, min_j, max_i, max_j = self.layout.state.get_extent()

        width = max_i - min_i + 3
        height = max_j - min_j + 3
        size = max(width, height)
        i = min_i - (size - (max_i - min_i + 1)) / 2.
        j = min_j - (size - (max_j - min_j + 1)) / 2.

        return self.layout.state.copy(
            i=i,
            j=j,
            scale=float(self._original_state.size)/size,
            size=size,
            size_origin=self.layout.state.size,
            background_factor=1.,
            top_bar_dy=1.,
            bottom_bar_dy=1.
        ), conf_anim_t()

    def _exit_transition(self) -> tuple[Optional[LayoutState], Optional[float]]:
        if self._original_state is None:
            return None, None

        i, j = self._original_state.i, self._original_state.j
        fi, fj, fw, fh = self.layout.find_focused_box()

        while fi < i:
            i -= 1
        while fj < j:
            j -= 1
        while fi >= i + self._original_state.size:
            i += 1
        while fj >= j + self._original_state.size:
            j += 1

        return self._original_state.copy(i=i, j=j), conf_anim_t()

    def on_key(self, time_msec: int, keycode: int, state: int, keysyms: str) -> bool:
        if state != PYWM_PRESSED and self.layout.mod_sym in keysyms:
            self.layout.exit_overlay()
            return True

        """
        For now capture all keys
        """
        return True
