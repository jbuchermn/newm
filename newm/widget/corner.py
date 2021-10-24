from __future__ import annotations
from typing import TYPE_CHECKING

import cairo
import math

from pywm import PyWMCairoWidget, PyWMWidgetDownstreamState, PyWMOutput

from ..config import configured_value

if TYPE_CHECKING:
    from newm.layout import Layout


conf_corner_radius = configured_value('corner_radius', 17.5)


class Corner(PyWMCairoWidget):
    def __init__(self, wm: Layout, output: PyWMOutput, left: bool, top: bool):
        self.r = conf_corner_radius()
        self.radius = round(output.scale * self.r)

        super().__init__(wm, output, self.radius, self.radius)

        self.left = left
        self.top = top

        self.render()

    def process(self) -> PyWMWidgetDownstreamState:
        result = PyWMWidgetDownstreamState()
        result.z_index = 100
        result.box = ((0 if self.left else self.output.width - self.r) + self.output.pos[0],
                      (0 if self.top else self.output.height - self.r) + self.output.pos[1],
                      self.r, self.r)
        return result

    def _render(self, surface: cairo.ImageSurface) -> None:
        ctx = cairo.Context(surface)

        ctx.set_source_rgba(.0, .0, .0, 1.)
        ctx.rectangle(0, 0, self.radius, self.radius)
        ctx.fill()

        ctx.set_operator(cairo.OPERATOR_CLEAR)
        ctx.arc(self.radius if self.left else 0, self.radius if self.top else 0, self.radius, 0, 2. * math.pi)
        ctx.fill()


