from __future__ import annotations
from typing import TYPE_CHECKING, Optional

import logging

from pywm import PYWM_RELEASED
from pywm.touchpad import GestureListener, LowpassGesture, HigherSwipeGesture
from pywm.touchpad.gestures import Gesture

from .overlay import Overlay
from ..config import configured_value

if TYPE_CHECKING:
    from ..layout import Layout
    from ..state import LayoutState


logger = logging.getLogger(__name__)

conf_gesture_factor = configured_value("launcher.gesture_factor", 200)
conf_anim_t = configured_value("anim_time", .3)

class LauncherOverlay(Overlay):
    def __init__(self, layout: Layout):
        super().__init__(layout)

        self._is_opened = False
        self._has_gesture = False

    def on_gesture(self, gesture: Gesture) -> bool:
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
                self._has_gesture = True
                return True

        else:
            """
            Initial gesture
            """
            LowpassGesture(gesture).listener(GestureListener(
                self._on_update,
                lambda: self._on_update(None)
            ))
            self._has_gesture = True
            return True

        return False


    def _on_update(self, values: Optional[dict[str, float]]) -> None:
        if self._is_opened == False:
            perc = values['delta2_s'] * conf_gesture_factor() if values is not None else 1
            self.layout.state.launcher_perc = max(min(perc, 1.0), 0.0)

            if values is None:
                self._is_opened = True
                for v in self.layout.panels():
                    if v.panel == "launcher":
                        v.focus()
        else:
            perc = 1. - (values['delta2_s'] * conf_gesture_factor() if values is not None else 1)
            self.layout.state.launcher_perc = max(min(perc, 1.0), 0.0)

            if values is None:
                self.layout.exit_overlay()

        self.layout.damage()


    def on_key(self, time_msec: int, keycode: int, state: int, keysyms: str) -> bool:
        if keysyms == "Escape" and state == PYWM_RELEASED:
            self.layout.exit_overlay()
            return True

        return False

    def _enter_transition(self) -> tuple[Optional[LayoutState], Optional[float]]:
        if self._has_gesture:
            return None, None

        logger.debug("Entering LauncherOverlay with animation...")
        return self.layout.state.copy(launcher_perc=1), conf_anim_t()

    def _exit_transition(self) -> tuple[Optional[LayoutState], Optional[float]]:
        logger.debug("Exiting LauncherOverlay with animation...")
        return self.layout.state.copy(launcher_perc=0), conf_anim_t()
