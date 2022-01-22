from __future__ import annotations
from typing import Callable, Union

from ..gesture import Gesture

class GestureProvider:
    def __init__(self, on_gesture: Callable[[Gesture], bool]) -> None:
        self._on_gesture = on_gesture

    """
    0 == False, let slip to next provider
    1 == False, don't let slip to next provider (client receives it)
    2 == True
    """
    def on_pywm_gesture(self, kind: str, time_msec: int, args: list[Union[float, int]]) -> int:
        return 0

    """
    0 == False, let slip to next provider
    1 == False, don't let slip to next provider (client receives it)
    2 == True
    """
    def on_pywm_motion(self, time_msec: int, delta_x: float, delta_y: float) -> int:
        return 0

    def on_pywm_axis(self, time_msec: int, source: int, orientation: int, delta: float, delta_discrete: int) -> int:
        return 0


    """
    Reset any non-captured running gesture to allow a potentially new one to start
    """
    def reset_gesture(self) -> None:
        pass

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass
