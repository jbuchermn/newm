from pywm import PYWM_RELEASED
from pywm.touchpad import GestureListener, LowpassGesture, HigherSwipeGesture
from .overlay import Overlay

class LauncherOverlay(Overlay):
    def __init__(self, layout):
        super().__init__(layout)

        self._launcher = None
        for view in self.layout.panels():
            if view.panel == "launcher":
                self._launcher = view
                break

        self._is_opened = False

    def on_gesture(self, gesture):
        if self._is_opened:
            if isinstance(gesture, HigherSwipeGesture) \
                    and gesture.n_touches == 5:
                """
                Final gesture
                """
                LowpassGesture(gesture).listener(GestureListener(
                    self._on_update,
                    lambda: self._on_update(None)
                ))

        else:
            """
            Initial gesture
            """
            LowpassGesture(gesture).listener(GestureListener(
                self._on_update,
                lambda: self._on_update(None)
            ))


    def _on_update(self, values):
        if self._is_opened == False:
            perc = values['delta2_s'] * 1000 if values is not None else 1
            self.layout.panel_endpoint.broadcast({
                'kind': 'activate_launcher',
                'value': perc
            })

            self._launcher.state.perc = perc
            self._launcher.damage()

            if values is None:
                self._is_opened = True
        else:
            perc = 1. - (values['delta2_s'] * 1000 if values is not None else 1)
            self.layout.panel_endpoint.broadcast({
                'kind': 'activate_launcher',
                'value': perc
            })

            self._launcher.state.perc = perc
            self._launcher.damage()

            if values is None:
                self._close()


    def on_key(self, time_msec, keycode, state, keysyms):
        if keysyms == "Escape" and state == PYWM_RELEASED:
            self._close()
            return True

        """
        For now capture all keys
        """
        return True

    def _close(self):
        if self._launcher is not None:
            new_state = self._launcher.state.copy()
            new_state.perc = 0.
            self._launcher.animate_to(new_state)

        self.layout.exit_overlay()

