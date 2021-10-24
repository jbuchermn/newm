from __future__ import annotations
from typing import TYPE_CHECKING

from abc import abstractmethod
from threading import Thread
import time
import cairo

from pywm import PyWMCairoWidget, PyWMWidgetDownstreamState, PyWMOutput

from ..interpolation import WidgetDownstreamInterpolation
from ..animate import Animate
from ..config import configured_value

if TYPE_CHECKING:
    from ..state import LayoutState
    from ..layout import Layout

conf_bar_height = configured_value('bar.height', 20)
conf_font_size = configured_value('bar.font_size', 12)

conf_top_bar_text = configured_value('bar.top_texts', lambda: ["1", "2", "3"])
conf_bottom_bar_text = configured_value('bar.bottom_texts', lambda: ["4", "5", "6"])
conf_font = configured_value('bar.font', 'Source Code Pro for Powerline')


class Bar(PyWMCairoWidget, Animate[PyWMWidgetDownstreamState]):
    def __init__(self, wm: Layout, output: PyWMOutput):
        PyWMCairoWidget.__init__(
            self, wm, output,
            int(output.scale * output.width),
            int(output.scale * conf_bar_height()))
        Animate.__init__(self)

        self._output: PyWMOutput = output

        self.texts = ["Leftp", "Middlep", "Rightp"]
        self.font_size = output.scale * conf_font_size()

    def set_texts(self, texts: list[str]) -> None:
        self.texts = texts
        self.render()

    def _render(self, surface: cairo.ImageSurface) -> None:
        ctx = cairo.Context(surface)

        ctx.set_source_rgba(.0, .0, .0, .7)
        ctx.rectangle(0, 0, self.width, self.height)
        ctx.fill()

        ctx.select_font_face(conf_font())
        ctx.set_font_size(self.font_size)

        _, y_bearing, c_width, c_height, _, _ = ctx.text_extents("pA")
        c_width /= 2

        total_text_width = sum([len(t) for t in self.texts])
        spacing = self.width - total_text_width * c_width
        spacing /= len(self.texts)

        x = spacing/2.
        for t in self.texts:
            ctx.move_to(x, self.height/2 - c_height/2 - y_bearing)
            ctx.set_source_rgb(1., 1., 1.)
            ctx.show_text(t)
            x += len(t) * c_width + spacing

        ctx.stroke()

    @abstractmethod
    def reducer(self, wm_state: LayoutState) -> PyWMWidgetDownstreamState:
        pass

    def animate(self, old_state: LayoutState, new_state: LayoutState, dt: float) -> None:
        cur = self.reducer(old_state)
        nxt = self.reducer(new_state)

        self._animate(WidgetDownstreamInterpolation(cur, nxt), dt)

    def process(self) -> PyWMWidgetDownstreamState:
        return self._process(self.reducer(self.wm.state))


class TopBar(Bar, Thread):
    def __init__(self, wm: Layout, output: PyWMOutput) -> None:
        Bar.__init__(self, wm, output)
        Thread.__init__(self)

        self._running = True
        self.start()

    def stop(self) -> None:
        self._running = False

    def reducer(self, wm_state: LayoutState) -> PyWMWidgetDownstreamState:
        result = PyWMWidgetDownstreamState()
        result.z_index = 5

        dy = wm_state.top_bar_dy * conf_bar_height()
        result.box = (self._output.pos[0], self._output.pos[1] + dy - conf_bar_height(), self.wm.width, conf_bar_height())

        return result

    def run(self) -> None:
        while self._running:
            self.set()
            time.sleep(1.)

    def set(self) -> None:
        self.set_texts(conf_top_bar_text()())

class BottomBar(Bar, Thread):
    def __init__(self, wm: Layout, output: PyWMOutput):
        Bar.__init__(self, wm, output)
        Thread.__init__(self)

        self._running = True
        self.start()

    def stop(self) -> None:
        self._running = False

    def reducer(self, wm_state: LayoutState) -> PyWMWidgetDownstreamState:
        result = PyWMWidgetDownstreamState()
        result.z_index = 5

        dy = wm_state.bottom_bar_dy * conf_bar_height()
        result.box = (self._output.pos[0], self._output.pos[1] + self._output.height - dy, self._output.width,
                      conf_bar_height())

        return result

    def run(self) -> None:
        while self._running:
            self.set()
            time.sleep(1.)

    def set(self) -> None:
        self.set_texts(conf_bottom_bar_text()())
