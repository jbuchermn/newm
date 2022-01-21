from __future__ import annotations
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..state import LayoutState
    from ..view import View, CustomDownstreamState
    from ..layout import Layout

import logging

from pywm import PyWMWidget, PyWMWidgetDownstreamState, PyWMOutput

from ..animate import Animate, Animatable
from ..interpolation import WidgetDownstreamInterpolation
from ..config import configured_value
from ..util import get_color

logger = logging.getLogger(__name__)

conf_view_corner_radius = configured_value('view.corner_radius', 12)
conf_ssd_w = configured_value('view.ssd.width', 2)
conf_enabled = configured_value('view.ssd.enabled', True)
conf_color = configured_value('view.ssd.color', '#BEBEBEFF')

class SSD(PyWMWidget, Animate[PyWMWidgetDownstreamState]):
    def __init__(self, wm: Layout, output: PyWMOutput, parent: SSDs):
        self._output = output
        self._parent = parent
        PyWMWidget.__init__(self, wm, output)
        Animate.__init__(self)

        self._corner_radius = -1.
        self.set_corner_radius(conf_view_corner_radius())

    def set_corner_radius(self, radius: float) -> None:
        if abs(radius - self._corner_radius) < 0.01:
            return
        self._corner_radius = radius
        self.set_primitive("rounded_corners_border", [], [
            # Color
            *get_color(conf_color()),
            # Corner radius
            self._corner_radius * self._output.scale,
            # Width
            conf_ssd_w() * self._output.scale])

    def reducer(self, state: CustomDownstreamState) -> PyWMWidgetDownstreamState:
        self.set_corner_radius(state.corner_radius)
        return PyWMWidgetDownstreamState(state.z_index + 0.1, state.logical_box, lock_enabled=False)

    def animate(self, old_state: CustomDownstreamState, new_state: CustomDownstreamState, dt: float) -> None:
        cur = self.reducer(old_state)
        nxt = self.reducer(new_state)

        self._animate(WidgetDownstreamInterpolation(self.wm, self, cur, nxt), dt)

    def process(self) -> PyWMWidgetDownstreamState:
        if self._parent.view_state is None:
            return PyWMWidgetDownstreamState()
        else:
            return self._process(self.reducer(self._parent.view_state))

class SSDs(Animatable):
    def __init__(self, wm: Layout, view: View):
        self.wm = wm
        self.view = view
        self.view_state: Optional[CustomDownstreamState] = None

        self.ssds: list[SSD] = []

        self.update()

    def update(self) -> None:
        self.destroy()
        if conf_enabled():
            self.ssds = [self.wm.create_widget(SSD, o, self) for o in self.wm.layout]

    def destroy(self) -> None:
        for b in self.ssds:
            b.destroy()
        self.ssds = []

    def animate(self, old_state: LayoutState, new_state: LayoutState, dt: float) -> None:
        if self.view.up_state is not None:
            view_old_down_state = self.view.reducer(self.view.up_state, old_state)
            view_new_down_state = self.view.reducer(self.view.up_state, new_state)

            self.view_state = view_new_down_state

            for b in self.ssds:
                b.animate(view_old_down_state, view_new_down_state, dt)

    def flush_animation(self) -> None:
        for b in self.ssds:
            b.flush_animation()

    def damage(self) -> None:
        if self.view.up_state is not None:
            self.view_state = self.view.reducer(self.view.up_state, self.wm.state)
        for b in self.ssds:
            b.damage()
