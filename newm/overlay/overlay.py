from __future__ import annotations
from typing import Optional, TYPE_CHECKING

import logging

from ..gestures import Gesture

if TYPE_CHECKING:
    from ..state import LayoutState
    from ..layout import Layout

logger = logging.getLogger(__name__)

class Overlay:
    def __init__(self, layout: Layout) -> None:
        self.layout = layout
        self._ready = False

    def ready(self) -> bool:
        return self._ready

    def init(self) -> None:
        wm_state, dt = self._enter_transition()
        if wm_state is not None and dt is not None:
            logger.debug("Overlay: Enter animation")
            self.layout.animate_to(lambda _: (None, wm_state), dt, self._enter_finished, overlay_safe=True)
        else:
            self._ready = True

        self.post_init()

    def _enter_finished(self) -> None:
        logger.debug("Overlay: Enter animation completed")
        self._ready = True

    def destroy(self) -> None:
        self.pre_destroy()

        self._ready = False
        wm_state, dt = self._exit_transition()
        if wm_state is not None and dt is not None:
            logger.debug("Overlay: Exit animation")
            self.layout.animate_to(lambda _: (None, wm_state), dt, self._exit_finished, overlay_safe=True)
        else:
            self.layout.on_overlay_destroyed()

    def _exit_finished(self) -> None:
        logger.debug("Overlay: Exit animation completed")
        self.layout.on_overlay_destroyed()


    """
    Virtual methods
    """

    def post_init(self) -> None:
        pass

    def pre_destroy(self) -> None:
        pass
    
    def _enter_transition(self) -> tuple[Optional[LayoutState], Optional[float]]:
        return None, 0

    def _exit_transition(self) -> tuple[Optional[LayoutState], Optional[float]]:
        return None, 0

    def on_key(self, time_msec: int, keycode: int, state: int, keysyms: str) -> bool:
        return True

    def on_modifiers(self, modifiers: int) -> bool:
        return False

    def on_motion(self, time_msec: int, delta_x: float, delta_y: float) -> bool:
        return False

    def on_button(self, time_msec: int, button: int, state: int) -> bool:
        return False

    def on_axis(self, time_msec: int, source: int, orientation: int, delta: float, delta_discrete: int) -> bool:
        return False

    def on_gesture(self, gesture: Gesture) -> bool:
        return False
