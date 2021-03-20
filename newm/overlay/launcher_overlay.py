import logging

from pywm import PYWM_RELEASED
from pywm.touchpad import GestureListener, LowpassGesture, HigherSwipeGesture
from .overlay import Overlay
from ..config import configured_value

logger = logging.getLogger(__name__)

conf_gesture_factor = configured_value("launcher.gesture_factor", 200)

class LauncherOverlay(Overlay):
    def __init__(self, layout):
        super().__init__(layout)

        self._is_opened = False

    def on_gesture(self, gesture):
        logger.debug("LauncherOverlay: new gesture")
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
            perc = values['delta2_s'] * conf_gesture_factor() if values is not None else 1
            self.layout.state.launcher_perc = max(min(perc, 1.0), 0.0)

            if values is None:
                self._is_opened = True
        else:
            perc = 1. - (values['delta2_s'] * conf_gesture_factor() if values is not None else 1)
            self.layout.state.launcher_perc = max(min(perc, 1.0), 0.0)

            if values is None:
                self.layout.exit_overlay()

        self.layout.damage()


    def on_key(self, time_msec, keycode, state, keysyms):
        if keysyms == "Escape" and state == PYWM_RELEASED:
            self.layout.exit_overlay()
            return True

        """
        For now capture all keys
        """
        return True

    def _exit_transition(self):
        logger.debug("Exiting LauncherOverlay with animation...")
        return self.layout.state.copy(launcher_perc=0), .3
