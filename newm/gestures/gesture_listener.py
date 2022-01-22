from __future__ import annotations
from typing import Optional, Callable

class GestureListener:
    def __init__(self, on_update: Optional[Callable[[dict[str, float]], None]], on_terminate: Optional[Callable[[], None]]):
        self._on_update = on_update
        self._on_terminate = on_terminate

    def update(self, values: dict[str, float]) -> None:
        if self._on_update is not None:
            self._on_update(values)

    def terminate(self) -> None:
        if self._on_terminate is not None:
            self._on_terminate()
