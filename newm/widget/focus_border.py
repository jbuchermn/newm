from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..state import LayoutState
    from ..layout import Layout, Workspace, WorkspaceState

import logging

from pywm import PyWMWidget, PyWMWidgetDownstreamState, PyWMOutput

logger = logging.getLogger(__name__)

class FocusBorder(PyWMWidget):
    def __init__(self, wm: Layout, output: PyWMOutput):
        self._output = output
        super().__init__(wm, output)

        self.set_primitive("rounded_corners_border", [], [
            # Color
            48./255., 213./255., 200./255., 0.7,
            # Corner radius
            16.5 * self._output.scale,
            # Width
            1. * self._output.scale])

    def process(self) -> PyWMWidgetDownstreamState:
        return PyWMWidgetDownstreamState(10, (1, 1, self._output.width - 2, self._output.height - 2))
