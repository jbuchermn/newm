from .overlay import Overlay, EnterOverlayTransition, ExitOverlayTransition


class OverviewOverlay(Overlay):
    def __init__(self, layout):
        super().__init__(layout)
        self._original_state = self.layout.state

    def _enter_transition(self):
        return EnterOverlayTransition(
            self, .2,
            i=self._original_state.min_i,
            j=self._original_state.min_j,
            size=max(self._original_state.max_i -
                     self._original_state.min_i + 1,
                     self._original_state.max_j -
                     self._original_state.min_j + 1),
            background_factor=1.
        )

    def _exit_transition(self):
        return ExitOverlayTransition(
            self, .2,
            **self._original_state.kwargs()
        )
