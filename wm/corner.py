import cairo
import math
from pywm import PyWMCairoWidget, PyWMWidgetDownstreamState


CORNER_RADIUS = 12.5


class Corner(PyWMCairoWidget):
    def __init__(self, wm, left, top):
        self.radius = int(wm.config['output_scale'] * CORNER_RADIUS)

        super().__init__(wm, self.radius, self.radius)

        self.left = left
        self.top = top

        self.render()

    def process(self):
        result = PyWMWidgetDownstreamState()
        result.z_index = 100
        result.box = (0 if self.left else self.wm.width - CORNER_RADIUS,
                      0 if self.top else self.wm.height - CORNER_RADIUS,
                      CORNER_RADIUS, CORNER_RADIUS)
        return result

    def _render(self, surface):
        ctx = cairo.Context(surface)

        ctx.set_source_rgba(.0, .0, .0, 1.)
        ctx.rectangle(0, 0, self.radius, self.radius)
        ctx.fill()

        ctx.set_operator(cairo.OPERATOR_CLEAR)
        ctx.arc(self.radius if self.left else 0, self.radius if self.top else 0, self.radius, 0, 2. * math.pi)
        ctx.fill()


