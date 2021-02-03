from pywm import PYWM_PRESSED

from .overlay import Overlay, EnterOverlayTransition, ExitOverlayTransition


class OverviewOverlay(Overlay):
    def __init__(self, layout):
        super().__init__(layout)
        self._original_state = self.layout.state

    def _enter_transition(self):
        width = self._original_state.max_i - self._original_state.min_i + 1
        height = self._original_state.max_j - self._original_state.min_j + 1
        i = self._original_state.min_i
        j = self._original_state.min_j

        return EnterOverlayTransition(
            self, .2,
            i=i,
            j=j,
            size=max(width, height),
            background_factor=1.,
            top_bar_dy=1.,
            bottom_bar_dy=1.
        )

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

        args = dict(self._original_state.kwargs())
        args['i'] = i
        args['j'] = j
        return ExitOverlayTransition(
            self, .2,
            **args
        )

    def on_key(self, time_msec, keycode, state, keysyms):
        if state != PYWM_PRESSED and self.layout.mod_sym in keysyms:
            self.layout.exit_overlay()
            return True
        return False
