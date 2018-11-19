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

        if width < height:
            i -= (height - width)/2.
        if width > height:
            j -= (width - height)/2.

        return EnterOverlayTransition(
            self, .4,
            i=i,
            j=j,
            size=max(width, height),
            background_factor=1.,
            top_bar_dy=1.,
            bottom_bar_dy=1.
        )

    def _exit_transition(self):
        return ExitOverlayTransition(
            self, .4,
            **self._original_state.kwargs()
        )
