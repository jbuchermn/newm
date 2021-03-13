from pywm import PYWM_PRESSED

from .overlay import Overlay


class OverviewOverlay(Overlay):
    def __init__(self, layout):
        super().__init__(layout)
        self._original_state = None

    def _enter_transition(self):
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
            background_factor=1.,
            top_bar_dy=1.,
            bottom_bar_dy=1.
        ), .3

    def _exit_transition(self):
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

        return self._original_state.copy(i=i, j=j), .3

    def on_key(self, time_msec, keycode, state, keysyms):
        if state != PYWM_PRESSED and self.layout.mod_sym in keysyms:
            self.layout.exit_overlay()
            return True

        """
        For now capture all keys
        """
        return True
