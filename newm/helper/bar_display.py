from __future__ import annotations
from typing import Optional

from abc import abstractmethod

from subprocess import Popen, PIPE, STDOUT
import logging

logger = logging.getLogger(__name__)

class BarDisplay:
    @abstractmethod
    def display(self, value: float) -> None:
        pass

class WobRunner(BarDisplay):
    def __init__(self, command: str="wob") -> None:
        self._command = command
        self._wob: Optional[Popen] = None

    def display(self, value: float) -> None:
        if self._wob is None or self._wob.poll() is not None:
            logger.debug("Restarting wob...")
            self._wob = Popen(self._command.split(" "), stdout=PIPE, stdin=PIPE, stderr=STDOUT)

        if self._wob.stdin is not None:
            self._wob.stdin.write(("%d\n" % round(value * 100)).encode("utf-8"))
            self._wob.stdin.flush()
