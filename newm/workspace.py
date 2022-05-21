from __future__ import annotations
from typing import Optional

from pywm import (
    PyWMOutput,
)

class Workspace:
    def __init__(self, output: PyWMOutput, pos_x: int, pos_y: int, width: int, height: int, prevent_anim: bool=False) -> None:
        self._handle = -1
        self.outputs = [output]

        self.pos_x = pos_x
        self.pos_y = pos_y
        self.width = width
        self.height = height

        self.prevent_anim = prevent_anim

        # Hint at view._handle to focus when switching to this workspace (not guaranteed to exist anymore)
        self.focus_view_hint: Optional[int] = None

    def swallow(self, other: Workspace) -> bool:
        if self.pos_x + self.width <= other.pos_x:
            return False
        if self.pos_y + self.height <= other.pos_y:
            return False
        if self.pos_x >= other.pos_x + other.width:
            return False
        if self.pos_y >= other.pos_y + other.height:
            return False

        pos_x = min(self.pos_x, other.pos_x)
        pos_y = min(self.pos_y, other.pos_y)
        width = max(self.pos_x + self.width, other.pos_x + other.width) - pos_x
        height = max(self.pos_y + self.height, other.pos_y + other.height) - pos_y
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.width = width
        self.height = height
        self.outputs += other.outputs
        self.prevent_anim |= other.prevent_anim

        return True

    def score(self, other: Workspace) -> float:
        x, y, w, h = self.pos_x, self.pos_y, self.width, self.height
        if other.pos_x > x:
            w -= (other.pos_x - x)
            x += (other.pos_x - x)
        if other.pos_y > y:
            h -= (other.pos_y - y)
            y += (other.pos_y - y)
        if x + w > other.pos_x + other.width:
            w -= (x + w - other.pos_x - other.width)
        if y + h > other.pos_y + other.height:
            h -= (y + h - other.pos_y - other.height)

        if w <= 0 or h <= 0:
            return 0

        return w*h / (self.width * self.height)

    def __str__(self) -> str:
        return "Workspace[%d] at %d, %d --> %d, %d (Outputs: %s)" % (
            self._handle,
            self.pos_x,
            self.pos_y,
            self.width,
            self.height,
            [o._key for o in self.outputs]
        )

