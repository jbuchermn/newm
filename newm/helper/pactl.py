from __future__ import annotations
from typing import Optional

import os
import re
import logging

from .wob_runner import WobRunner
from .execute import execute

logger = logging.getLogger(__name__)


class PaCtl:
    def __init__(self, sink: int=0, wob_runner: Optional[WobRunner]=None) -> None:
        self._sink = sink
        self._wob_runner = wob_runner
        self._matcher = re.compile(r".*?(\d+)%.*")

    def mute(self) -> None:
        os.system("pactl set-sink-mute %d toggle &" % self._sink)
        if self._wob_runner is not None:
            self._wob_runner.display(0.)

    def volume_adj(self, perc: int) -> None:
        os.system("pactl set-sink-volume %d %+d%% &" % (self._sink, perc))
        if self._wob_runner is not None:
            vol = execute("pactl list sinks | grep '^[[:space:]]Volume:' | head -n $(( %d + 1 )) | tail -n 1" % self._sink)
            match = self._matcher.match(vol)
            if match is not None:
                self._wob_runner.display(float(match.group(1))/100.)


