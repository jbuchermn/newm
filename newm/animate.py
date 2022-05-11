from __future__ import annotations
from typing import TypeVar, Generic, Optional

from abc import abstractmethod
import logging
import time
from threading import Lock

from .interpolation import Interpolation
from .state import LayoutState


logger = logging.getLogger(__name__)

StateT = TypeVar('StateT')

class Animatable:
    @abstractmethod
    def flush_animation(self) -> None:
        pass
    @abstractmethod
    def animate(self, old_state: LayoutState, new_state: LayoutState, dt: float) -> None:
        pass

class Animate(Generic[StateT]):
    def __init__(self) -> None:
        self._animation: Optional[tuple[Interpolation[StateT], float, float, float, int]] = None
        self._animation_lock = Lock()

    def _process(self, default_state: StateT) -> StateT:
        with self._animation_lock:
            if self._animation is not None:
                interpolation, s, d, last_ts, frame = self._animation
                frame += 1

                if frame == 1:
                    t = time.time()
                    s = t - 1./120.

                ts = time.time()
                self._animation = interpolation, s, d, ts, frame

                perc = min((ts - s) / d, 1.0)

                self._anim_damage()
                return interpolation.get(perc)
            else:
                return default_state

    def flush_animation(self) -> None:
        with self._animation_lock:
            self._animation = None

    def _animate(self, interp: Interpolation[StateT], dt: float) -> None:
        self._animation = (interp, -1, dt, -1, 0)
        self._anim_damage()

    def get_final_time(self) -> Optional[float]:
        if self._animation is not None and self._animation[1] > 0.:
            return self._animation[1] + self._animation[2]
        return None

    @abstractmethod
    def _anim_damage(self) -> None:
        pass
