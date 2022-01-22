from __future__ import annotations
from typing import Union

import logging

from .provider import GestureProvider

logger = logging.getLogger(__name__)

"""
At the moment libinput is not able to properly handle gestures at all, e.g. any two-finger gesture which is not
very explicitly pinch, does not get reported at all - maybe some day this changes.
"""
class CGestureProvider(GestureProvider):
    def on_pywm_gesture(self, kind: str, time_msec: int, args: list[Union[float, str]]) -> bool:
        logger.debug("GESTURE - %s: %s" % (kind, args))
        return False

    def on_pywm_motion(self, time_msec: int, delta_x: float, delta_y: float) -> bool:
        logger.debug("GESTURE - %s: %s" % ("motion", (delta_x, delta_y)))
        return False
