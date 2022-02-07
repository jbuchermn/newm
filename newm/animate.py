from __future__ import annotations
from typing import TypeVar, Generic, Optional

from abc import abstractmethod
import logging
import time
from threading import Lock

from .interpolation import Interpolation
from .state import LayoutState
from .config import configured_value


logger = logging.getLogger(__name__)

StateT = TypeVar('StateT')

conf_debug_freq = configured_value('debug.animation_frequency', 58.)

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
                    s, last_ts = t - 1./120., t - 1./120.

                ts = time.time()
                if ts - last_ts > 1. / conf_debug_freq():
                    logger.debug("TIMER(%20s, %s): Slow animation frame (%2d): %.2fms = %.2ffps", self.__class__.__name__, id(self), frame, 1000. * (ts-last_ts), 1. / (ts-last_ts))
                self._animation = interpolation, s, d, ts, frame

                perc = min((ts - s) / d, 1.0)

                self.damage_in_animation()
                return interpolation.get(perc)
            else:
                return default_state

    def flush_animation(self) -> None:
        with self._animation_lock:
            self._animation = None

    def _animate(self, interp: Interpolation[StateT], dt: float) -> None:
        self._animation = (interp, -1, dt, -1, 0)
        self.damage_in_animation()

    def get_final_time(self) -> Optional[float]:
        if self._animation is not None and self._animation[1] > 0.:
            return self._animation[1] + self._animation[2]
        return None

    @abstractmethod
    def damage_in_animation(self) -> None:
        pass
