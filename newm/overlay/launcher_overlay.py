from __future__ import annotations
from typing import TYPE_CHECKING, Optional

import logging

from pywm import PYWM_RELEASED
from ..gestures import Gesture, GestureListener, LowpassGesture

from .overlay import Overlay
from ..config import configured_value

if TYPE_CHECKING:
    from ..layout import Layout
    from ..state import LayoutState


logger = logging.getLogger(__name__)

conf_gesture_factor = configured_value("panels.launcher.gesture_factor", 200)
conf_anim_t = configured_value("anim_time", .3)

conf_lp_freq = configured_value('gestures.lp_freq', 60.)
conf_lp_inertia = configured_value('gestures.lp_inertia', .8)

conf_gesture_binding_launcher = configured_value('gesture_bindings.launcher', (None, 'swipe-5'))

class LauncherOverlay(Overlay):
    def __init__(self, layout: Layout):
        super().__init__(layout)

        self._is_opened = False
        self._has_gesture = False

    def on_gesture(self, gesture: Gesture) -> bool:
        logger.debug("LauncherOverlay: new gesture")
        if self._is_opened:
            if gesture.kind == conf_gesture_binding_launcher()[1]:
                """
                Final gesture
                """
                LowpassGesture(gesture, conf_lp_inertia(), conf_lp_freq()).listener(GestureListener(
                    self._on_update,
                    lambda: self._on_update(None)
                ))
                self._has_gesture = True
                return True

        else:
            if gesture.kind == conf_gesture_binding_launcher()[1]:
                """
                Initial gesture
                """
                LowpassGesture(gesture, conf_lp_inertia(), conf_lp_freq()).listener(GestureListener(
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
        if keysyms == "Escape":
            if state == PYWM_RELEASED:
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

    def post_init(self) -> None:
        launcher = [v for v in self.layout.panels() if v.panel == "launcher"]
        if len(launcher) > 0:
            launcher[0].focus()
        else:
            logger.exception("Could not find launcher")
