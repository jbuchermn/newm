from __future__ import annotations
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..state import LayoutState
    from ..view import View
    from ..layout import Layout, Workspace, WorkspaceState

import logging

from pywm import PyWMWidget, PyWMWidgetDownstreamState, PyWMOutput

from ..animate import Animate
from ..interpolation import WidgetDownstreamInterpolation
from ..config import configured_value

logger = logging.getLogger(__name__)

conf_view_corner_radius = configured_value('view.corner_radius', 12)
conf_focus_d = configured_value('focus.distance', 4)
conf_focus_w = configured_value('focus.width', 2)
conf_anim_time = configured_value('focus.anim_time', 0.3)
conf_animate_on_change = configured_value('focus.animate_on_change', False)

class FocusBorder(PyWMWidget, Animate[PyWMWidgetDownstreamState]):
    def __init__(self, wm: Layout, output: PyWMOutput, parent: FocusBorders):
        self._output = output
        self._parent = parent
        PyWMWidget.__init__(self, wm, output)
        Animate.__init__(self)

        self.set_primitive("rounded_corners_border", [], [
            # Color
            48./255., 213./255., 200./255., 0.3,
            # Corner radius
            (conf_view_corner_radius() + conf_focus_d()) * self._output.scale,
            # Width
            conf_focus_w() * self._output.scale])

    def reducer(self, box: tuple[int, float, float, float, float]) -> PyWMWidgetDownstreamState:
        if box[0] == -999:
            return PyWMWidgetDownstreamState(0, (self._output.pos[0] - conf_focus_d(), self._output.pos[1] - conf_focus_d(), self._output.width + 2*conf_focus_d(), self._output.height + 2*conf_focus_d()))
        else:
            return PyWMWidgetDownstreamState(box[0], (box[1] - conf_focus_d(), box[2] - conf_focus_d(), box[3] + 2*conf_focus_d(), box[4] + 2*conf_focus_d()))

    def animate(self, old_box: tuple[int, float, float, float, float], new_box: tuple[int, float, float, float, float], dt: float) -> None:
        cur = self.reducer(old_box)
        nxt = self.reducer(new_box)

        self._animate(WidgetDownstreamInterpolation(self.wm, self, cur, nxt), dt)

    def process(self) -> PyWMWidgetDownstreamState:
        return self._process(self.reducer(self._parent.current_box))

class FocusBorders:
    def __init__(self, wm: Layout):
        self.wm = wm
        self.borders: list[FocusBorder] = []

        self._skip_next_animate: bool = False

        # -999 as a special value to signal no focus
        self.current_view: Optional[View] = None
        self.current_box: tuple[int, float, float, float, float] = -999, 0, 0, 0, 0

    def update(self) -> None:
        for b in self.borders:
            b.destroy()
        self.borders = [self.wm.create_widget(FocusBorder, o, self) for o in self.wm.layout]

    def _set_box(self, layout_state: Optional[LayoutState]=None) -> None:
        if layout_state is None:
            layout_state = self.wm.state

        if self.current_view is not None and self.current_view.up_state is not None:
            view_down_state = self.current_view.reducer(self.current_view.up_state, layout_state)
            self.current_box = view_down_state.z_index - 1, view_down_state.box[0] + self.current_view.up_state.offset[0], view_down_state.box[1] + self.current_view.up_state.offset[1], view_down_state.box[2], view_down_state.box[3]
        else:
            self.current_box = -999, 0, 0, 0, 0

    def update_focus(self, view: View, present_states: Optional[tuple[Optional[LayoutState], Optional[LayoutState]]]=None) -> None:
        if id(view) == id(self.current_view):
            return

        animate = conf_animate_on_change()
        if present_states is not None:
            self._skip_next_animate = True
            animate = True

        old_box = self.current_box
        self.current_view = view
        self._set_box(layout_state=present_states[1] if present_states is not None else None)
        new_box = self.current_box

        if animate:
            for b in self.borders:
                b.animate(old_box, new_box, conf_anim_time())
        else:
            self.damage()

    def unfocus(self) -> None:
        self._skip_next_animate = True
        old_box = self.current_box
        self.current_view = None
        self._set_box()
        new_box = self.current_box

        for b in self.borders:
            b.animate(old_box, new_box, conf_anim_time())

    def animate(self, old_state: LayoutState, new_state: LayoutState, dt: float) -> None:
        if self._skip_next_animate:
            self._skip_next_animate = False
            return

        if self.current_view is not None and self.current_view.up_state is not None:
            view_old_down_state = self.current_view.reducer(self.current_view.up_state, old_state)
            view_new_down_state = self.current_view.reducer(self.current_view.up_state, new_state)

            old_box = view_old_down_state.z_index, *view_old_down_state.box
            new_box = view_new_down_state.z_index, *view_new_down_state.box

            self.current_box = new_box
            for b in self.borders:
                b.animate(old_box, new_box, dt)

    def damage(self) -> None:
        self._set_box()

        for b in self.borders:
            b.damage()
