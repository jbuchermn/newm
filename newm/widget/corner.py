from __future__ import annotations
from typing import TYPE_CHECKING

from pywm import PyWMWidget, PyWMWidgetDownstreamState, PyWMOutput

from ..config import configured_value

if TYPE_CHECKING:
    from newm.layout import Layout


conf_corner_radius = configured_value('corner_radius', 18)


class Corner(PyWMWidget):
    def __init__(self, wm: Layout, output: PyWMOutput, left: bool, top: bool):
        self.r = conf_corner_radius()
        self.radius = round(output.scale * self.r)

        super().__init__(wm, output)
        self._output: PyWMOutput = output

        self.left = left
        self.top = top

        i = 2 if top else 0
        if left:
            i += 1
        self.set_primitive("corner", [i], [self.radius, 0., 0., 0.])

    def process(self) -> PyWMWidgetDownstreamState:
        result = PyWMWidgetDownstreamState()
        result.z_index = 100000
        result.box = ((0 if self.left else self._output.width - self.r) + self._output.pos[0],
                      (0 if self.top else self._output.height - self.r) + self._output.pos[1],
                      self.r, self.r)
        return result
