from __future__ import annotations
from typing import TypeVar, Generic, Optional

from abc import abstractmethod
import logging
import time

from .interpolation import Interpolation

logger = logging.getLogger(__name__)

StateT = TypeVar('StateT')

class Animate(Generic[StateT]):
    def __init__(self) -> None:
        self._animation: Optional[tuple[Interpolation[StateT], float, float, float]] = None

    def _process(self, default_state: StateT) -> StateT:
        if self._animation is not None:
            interpolation, s, d, last_ts = self._animation
            ts = time.time()
            if ts - last_ts > 1. / 50.:
                logger.debug("Slow animation frame: %.2ffps", (1. / (ts-last_ts)))
            self._animation = (interpolation, s, d, ts)

            perc = min((ts - s) / d, 1.0)

            if perc >= 0.99999:
                self._animation = None

            self.damage()
            return interpolation.get(perc)
        else:
            return default_state

    def _animate(self, interp: Interpolation[StateT], dt: float) -> None:
        self._animation = (interp, time.time(), dt, time.time())
        self.damage()

    @abstractmethod
    def damage(self) -> None:
        pass
