from pywm import PYWM_PRESSED

from .overlay import Overlay


class OverviewOverlay(Overlay):
    def __init__(self, layout):
        super().__init__(layout)
        self._original_state = self.layout.state

    def _enter_transition(self):
        new_state = self._original_state.copy()
        new_state.width = new_state.max_i - new_state.min_i + 1
        new_state.height = new_state.max_j - new_state.min_j + 1
        new_state.i = self._original_state.min_i
        new_state.j = self._original_state.min_j
        new_state.size = max(new_state.width, new_state.height)
        new_state.background_factor = 1.
        new_state.top_bar_dy = 1.
        new_state.bottom_bar_dy = 1.

        return new_state

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

        new_state = self._original_state.copy()
        new_state.i = i
        new_state.j = j
        return new_state

    def on_key(self, time_msec, keycode, state, keysyms):
        if state != PYWM_PRESSED and self.layout.mod_sym in keysyms:
            self.layout.exit_overlay()
            return True

        """
        For now capture all keys
        """
        return True
