from __future__ import annotations
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..state import LayoutState
    from ..view import View, CustomDownstreamState
    from ..layout import Layout

import logging

from pywm import PyWMBlurWidget, PyWMWidgetDownstreamState, PyWMOutput

from ..animate import Animate, Animatable
from ..interpolation import WidgetDownstreamInterpolation

logger = logging.getLogger(__name__)


class BackgroundBlur(PyWMBlurWidget, Animate[PyWMWidgetDownstreamState], Animatable):
    def __init__(self, wm: Layout, output: PyWMOutput, view: View, radius: int, passes: int):
        PyWMBlurWidget.__init__(self, wm, output)
        Animate.__init__(self)

        self.set_blur(radius, passes)

        self.view = view
        self.view_state: Optional[CustomDownstreamState] = None

    def reducer(self, state: CustomDownstreamState) -> PyWMWidgetDownstreamState:
        return PyWMWidgetDownstreamState(state.z_index -0.001, state.logical_box, lock_enabled=False, opacity=1., corner_radius=state.corner_radius)

    def animate(self, old_state: LayoutState, new_state: LayoutState, dt: float) -> None:
        if self.view.up_state is not None:
            view_old_down_state = self.view.reducer(self.view.up_state, old_state)
            view_new_down_state = self.view.reducer(self.view.up_state, new_state)

            self.view_state = view_new_down_state

            cur = self.reducer(view_old_down_state)
            nxt = self.reducer(view_new_down_state)

            self._animate(WidgetDownstreamInterpolation(self.wm, self, cur, nxt), dt)

    def process(self) -> PyWMWidgetDownstreamState:
        if self.view_state is None:
            return PyWMWidgetDownstreamState()
        else:
            return self._process(self.reducer(self.view_state))

    def damage(self) -> None:
        if self.view.up_state is not None:
            self.view_state = self.view.reducer(self.view.up_state, self.wm.state)
        super().damage()

    def damage_in_animation(self) -> None:
        super().damage()
