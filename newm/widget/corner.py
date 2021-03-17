import cairo
import math
from pywm import PyWMCairoWidget, PyWMWidgetDownstreamState
from ..config import configured_value


conf_corner_radius = configured_value('corner_radius', 17.5)


class Corner(PyWMCairoWidget):
    def __init__(self, wm, left, top):
        self.r = conf_corner_radius()
        self.radius = int(wm.output_scale * self.r)

        super().__init__(wm, self.radius, self.radius)

        self.left = left
        self.top = top

        self.render()

    def process(self):
        result = PyWMWidgetDownstreamState()
        result.z_index = 100
        result.box = (0 if self.left else self.wm.width - self.r,
                      0 if self.top else self.wm.height - self.r,
                      self.r, self.r)
        return result

    def _render(self, surface):
        ctx = cairo.Context(surface)

        ctx.set_source_rgba(.0, .0, .0, 1.)
        ctx.rectangle(0, 0, self.radius, self.radius)
        ctx.fill()

        ctx.set_operator(cairo.OPERATOR_CLEAR)
        ctx.arc(self.radius if self.left else 0, self.radius if self.top else 0, self.radius, 0, 2. * math.pi)
        ctx.fill()


