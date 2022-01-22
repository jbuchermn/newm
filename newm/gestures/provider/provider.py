from __future__ import annotations
from typing import Callable, Union

from ..gesture import Gesture

class GestureProvider:
    def __init__(self, on_gesture: Callable[[Gesture], bool]) -> None:
        self._on_gesture = on_gesture

    def on_pywm_gesture(self, kind: str, time_msec: int, args: list[Union[float, str]]) -> bool:
        return False

    def on_pywm_motion(self, time_msec: int, delta_x: float, delta_y: float) -> bool:
        return False

    def on_pywm_axis(self, time_msec: int, source: int, orientation: int, delta: float, delta_discrete: int) -> bool:
        return False


    """
    Reset any non-captured running gesture to allow a potentially new one to start
    """
    def reset_gesture(self) -> None:
        pass

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass
