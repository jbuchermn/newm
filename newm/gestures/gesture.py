from __future__ import annotations

from .gesture_listener import GestureListener

"""
Kinds:
    - move-1
    - swipe-[2,3,4,5]

Values:
    - delta_x
    - delta_y
    - delta2_s
    - rotation
    - scale
"""
class Gesture:
    def __init__(self, kind: str) -> None:
        self._listeners: list[GestureListener] = []
        self.kind = kind

    def listener(self, l: GestureListener) -> None:
        self._listeners += [l]

    def _terminate(self) -> None:
        for l in self._listeners:
            l.terminate()

    def _update(self, values: dict[str, float]) -> None:
        for l in self._listeners:
            l.update(values)

    def __str__(self) -> str:
        return "Gesture(%s)" % self.kind
