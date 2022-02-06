from __future__ import annotations
from typing import TypeVar, Generic, Optional

from abc import abstractmethod
import logging
import time

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
        self._animation: Optional[tuple[Interpolation[StateT], float, float, float]] = None

    def _process(self, default_state: StateT) -> StateT:
        if self._animation is not None:
            if self._animation[1] <  0:
                t = time.time()
                self._animation = self._animation[0], t - 1./120., self._animation[2], t - 1./120.

            interpolation, s, d, last_ts = self._animation
            ts = time.time()
            if ts - last_ts > 1. / conf_debug_freq():
                logger.debug("Animate (%30s, %s) - Slow animation frame: %.2ffps", self.__class__.__name__, id(self), 1. / (ts-last_ts))
            self._animation = (interpolation, s, d, ts)

            perc = min((ts - s) / d, 1.0)

            self.damage()
            return interpolation.get(perc)
        else:
            return default_state

    def flush_animation(self) -> None:
        self._animation = None

    def _animate(self, interp: Interpolation[StateT], dt: float) -> None:
        self._animation = (interp, -1, dt, -1)
        self.damage()

    def get_final_time(self) -> Optional[float]:
        if self._animation is not None and self._animation[1] > 0.:
            return self._animation[1] + self._animation[2]
        return None

    @abstractmethod
    def damage(self) -> None:
        pass
