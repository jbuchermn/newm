from __future__ import annotations
from typing import Optional, TYPE_CHECKING, cast, TypeVar

import math
import logging

from pywm import PyWMView, PyWMViewDownstreamState
from pywm.pywm import PyWMDownstreamState
from pywm.pywm_view import PyWMViewUpstreamState

from .state import ViewState, LayoutState
from .interpolation import ViewDownstreamInterpolation
from .animate import Animate
from .overlay import MoveResizeFloatingOverlay
from .config import configured_value

if TYPE_CHECKING:
    from .layout import Layout
else:
    Layout = TypeVar('Layout')


logger = logging.getLogger(__name__)

conf_xwayland_css = configured_value('view.xwayland_handle_scale_clientside', False)
conf_corner_radius = configured_value('view.corner_radius', 12.5)
conf_padding = configured_value('view.padding', 8)
conf_fullscreen_padding = configured_value('view.fullscreen_padding', 0)

conf_panel_lock_h = configured_value('panels.lock.h', 0.5)
conf_panel_lock_w = configured_value('panels.lock.w', 0.5)
conf_panel_lock_corner_radius = configured_value('panels.lock.corner_radius', 50)
conf_panel_launcher_h = configured_value('panels.launcher.h', 0.8)
conf_panel_launcher_w = configured_value('panels.launcher.w', 0.8)
conf_panel_launcher_corner_radius = configured_value('panels.launcher.corner_radius', 0)

class View(PyWMView[Layout], Animate[PyWMViewDownstreamState]):
    def __init__(self, wm: Layout, handle: int):
        PyWMView.__init__(self, wm, handle)
        Animate.__init__(self)

        self.client_side_scale = 1.

        self.panel: Optional[str] = None

    def __str__(self) -> str:
        if self.up_state is None:
            return "<View %d>" % self._handle

        return "<View %d (%s): %s, %s, %s, %s, xwayland=%s, floating=%s>" % (
            self._handle, ("child(%d)" % self.parent._handle) if self.parent is not None else "root",
             self.up_state.title, self.app_id, self.role, self.pid,
             self.is_xwayland, self.up_state.is_floating)

    def is_dialog(self) -> bool:
        if self.up_state is None:
            return True

        return self.panel is None and self.up_state.is_floating

    def is_window(self) -> bool:
        if self.up_state is None:
            return False

        return self.panel is None and not self.up_state.is_floating

    def is_panel(self) -> bool:
        return self.panel is not None

    def main(self, state: LayoutState) -> tuple[Optional[LayoutState], Optional[LayoutState]]:
        logger.info("Init: %s", self)

        try:
            if conf_xwayland_css():
                if self.is_xwayland:
                    """
                    xwayland_handle_scale_clientside means clients should know and handle HiDPI-scale (e.g. --force-device-scale-factor=2)
                    and are thereforee set to scale 1 serverside
                    - this cannot work with multi-dpi setups and therefore is only a hack
                    - it does not work in conjunction with xdg_output_manager, since the output_manager exposes logical pixels
                        and XWayland does not handle that properly (result: mouse movements beyond screen_dimensions / output_scale will get truncated)
                    - Maybe XWayland will get smarter in the future: https://github.com/swaywm/wlroots/pull/2064 and
                        https://gitlab.freedesktop.org/xorg/xserver/-/merge_requests/432
                    - Then again, the future should by without X11/XWayland
                    """
                    self.client_side_scale = self.wm.output_scale
        except:
            pass

        if self.pid is not None:
            self.panel = self.wm.panel_launcher.get_panel_for_pid(self.pid)

        if self.panel is not None:
            logger.debug("Registered panel %s: %s", self.app_id, self.panel)

            self.damage()
            return None, None
        else:
            second_state = None

            """
            Place initially
            """
            if self.up_state is not None and self.up_state.is_floating:
                min_w, _, min_h, _ = [float(r) for r in self.up_state.size_constraints]

                if (min_w, min_h) == (0., 0.):
                    (min_w, min_h) = self.up_state.size

                if min_w == 0 or min_h == 0:
                    return None, None

                ci = state.i + state.size / 2.
                cj = state.j + state.size / 2.
                if self.parent is not None:
                    try:
                        ci = state.get_view_state(cast(View, self.parent)).i + state.get_view_state(cast(View, self.parent)).w / 2.
                        cj = state.get_view_state(cast(View, self.parent)).j + state.get_view_state(cast(View, self.parent)).h / 2.
                    except:
                        logger.warn("Unexpected: Could not access parent %s state" % self.parent)

                w, h = float(min_w), float(min_h)
                w *= state.size / self.wm.width / self.client_side_scale
                h *= state.size / self.wm.height / self.client_side_scale

                i = ci - w / 2.
                j = cj - h / 2.
                w = w
                h = h

                second_state = (i, j, w, h)

                self.focus()

            else:
                min_w, _, min_h, _ = [float(r) for r in self.up_state.size_constraints] if self.up_state is not None else (0., 0., 0., 0.)
                min_w *= state.size / self.wm.width / self.client_side_scale
                min_h *= state.size / self.wm.height / self.client_side_scale

                w = max(math.ceil(min_w), 1)
                h = max(math.ceil(min_h), 1)
                i, j = self.wm.place_initial(w, h)

                second_state = (i, j, w, h)

                self.focus()

            """
            Present
            """
            i, j, w, h = second_state
            i1, j1, w1, h1 = second_state

            i += .5*w
            j += .5*h
            w = 0
            h = 0


            state1 = state.with_view_state(
                    self,
                    is_tiled=not (self.up_state is not None and self.up_state.is_floating), i=i, j=j, w=w, h=h,
                    scale_origin=(w1, h1), move_origin=(i1, j1),
                    stack_idx=self._handle
            )

            state2 = state1.replacing_view_state(
                    self,
                    i=i1, j=j1, w=w1, h=h1, scale_origin=(None, None), move_origin=(None, None)
                ).focusing_view(self)

            return state1, state2

    def destroy(self) -> None:
        self.wm.destroy_view(self)

    def reducer(self, up_state: PyWMViewUpstreamState, state: LayoutState) -> PyWMViewDownstreamState:
        result = PyWMViewDownstreamState()

        if self.panel == "notifiers":
            result.z_index = 6
            result.accepts_input = False
            result.lock_enabled = True

            result.size = (
                int(self.wm.width * 0.2 * self.client_side_scale),
                int(self.wm.height * 0.3 * self.client_side_scale))

            result.box = (
                self.wm.width * 0.4,
                self.wm.height * 0.7,
                self.wm.width * 0.2,
                self.wm.height * 0.3)

        elif self.panel == "launcher":
            result.z_index = 5
            result.accepts_input = True
            result.corner_radius = conf_panel_launcher_corner_radius()

            result.size = (
                round(self.wm.width * conf_panel_launcher_w() * self.client_side_scale),
                round(self.wm.height * conf_panel_launcher_h() * self.client_side_scale))

            result.box = (
                (self.wm.width - result.size[0] / self.client_side_scale) / 2.,
                (self.wm.height - result.size[1] / self.client_side_scale) / 2. + (1. - state.launcher_perc) * self.wm.height,
                result.size[0] / self.client_side_scale,
                result.size[1] / self.client_side_scale)



        elif self.panel == "lock":
            result.z_index = 100
            result.accepts_input = True
            result.corner_radius = conf_panel_lock_corner_radius()
            result.lock_enabled = True

            result.size = (
                round(self.wm.width * conf_panel_lock_w() * self.client_side_scale),
                round(self.wm.height * conf_panel_lock_h() * self.client_side_scale))

            result.box = (
                (self.wm.width - result.size[0] / self.client_side_scale) / 2.,
                (self.wm.height - result.size[1] / self.client_side_scale) / 2. + (1. - state.lock_perc) * self.wm.height,
                result.size[0] / self.client_side_scale,
                result.size[1] / self.client_side_scale)

        else:
            result.accepts_input = True
            result.corner_radius = conf_corner_radius() if self.parent is None else 0

            if state.is_fullscreen() and conf_fullscreen_padding() == 0:
                result.corner_radius = 0

            """
            z_index based on hierarchy
            """
            depth = 0
            p = self.parent
            while p is not None:
                depth += 1
                p = p.parent

            result.z_index = depth + (2 if up_state.is_floating else 0)

            """
            Keep focused view on top
            """
            if self.is_focused():
                result.z_index += 1


            self_state = None
            stack_idx, stack_len = 0, 1
            try:
                self_state = state.get_view_state(self)
                _, stack_idx, stack_len = self_state.stack_data
            except Exception:
                """
                This can happen, if main has not been executed yet
                (e.g. during an overlay) - just return a box not displayed
                """
                logger.exception("Could not access view %s state" % self)
                return result


            """
            Handle box
            """
            i = self_state.i
            j = self_state.j
            w = self_state.w
            h = self_state.h

            if stack_len > 1:
                i += 0.05 * stack_idx / (stack_len - 1)
                j += 0.05 * self.wm.width / self.wm.height * stack_idx / (stack_len - 1)
                w -= 0.05
                h -= 0.05 * self.wm.width / self.wm.height

            x = i - state.i
            y = j - state.j

            x *= self.wm.width / state.size
            y *= self.wm.height / state.size
            w *= self.wm.width / state.size
            h *= self.wm.height / state.size

            padding = conf_fullscreen_padding() if state.is_fullscreen() else conf_padding()

            if w != 0 and h != 0:
                x += padding
                y += padding
                w -= 2*padding
                h -= 2*padding

            if up_state.size[0] > 0 and up_state.size[1] > 0:
                x -= up_state.offset[0] / up_state.size[0] * w
                y -= up_state.offset[1] / up_state.size[1] * h

            x, y, w, h = (x, y, w, h)

            """
            Handle client size
            """
            w_for_size, h_for_size = self_state.scale_origin
            if w_for_size is None or h_for_size is None:
                w_for_size, h_for_size = self_state.w, self_state.h

            size = state.size_origin if state.size_origin is not None else state.size

            w_for_size *= self.wm.width / size
            h_for_size *= self.wm.height / size
            w_for_size -= 2*padding
            h_for_size -= 2*padding

            width = math.ceil(w_for_size * self.client_side_scale)
            height = math.ceil(h_for_size * self.client_side_scale)

            result.size = (width, height)

            if up_state.is_floating:
                """
                Override: Keep floating windows scaled correctly
                """
                w = up_state.size[0] / self.client_side_scale * size / state.size
                h = up_state.size[1] / self.client_side_scale * size / state.size

            else:
                """
                Override: Keep aspect-ratio of windows
                """
                min_w, max_w, min_h, max_h = up_state.size_constraints
                width, height = result.size

                if width < min_w and min_w > 0:
                    width = min_w
                if width > max_w and max_w > 0:
                    width = max_w
                if height < min_h and min_h > 0:
                    height = min_h
                if height > max_h and max_h > 0:
                    width = min_w

                old_ar = result.size[1] / result.size[0] if result.size[0] > 0 else 1.
                new_ar = height / width if width > 0 else 1.

                if abs(old_ar - new_ar) > 0.001:
                    if new_ar < old_ar:
                        # new width is larger - would appear scaled up vertically
                        h *= new_ar / old_ar
                    else:
                        # new width is smaller - would appear scaled up horizontally
                        w *= old_ar / new_ar

                result.size = (width, height)

            result.box = (x, y, w, h)

            if 0.99 < result.box[2] / result.size[0] < 1.01:
                if result.box[2] != result.size[0]:
                    logger.debug("Potential scaling issue (%s): w = %f != %d", self.app_id, result.box[2], result.size[0])
            if 0.99 < result.box[3] / result.size[1] < 1.01:
                if result.box[3] != result.size[1]:
                    logger.debug("Potential scaling issue (%s): h = %f != %d", self.app_id, result.box[3], result.size[1])


        result.opacity = 1.0 if (result.lock_enabled and not state.final) else state.background_opacity
        return result


    def animate(self, old_state: LayoutState, new_state: LayoutState, dt: float) -> None:
        if self.up_state is None:
            return

        cur = self.reducer(self.up_state, old_state)
        nxt = self.reducer(self.up_state, new_state)

        self._animate(ViewDownstreamInterpolation(cur, nxt), dt)

    def process(self, up_state: PyWMViewUpstreamState) -> PyWMViewDownstreamState:
        return self._process(self.reducer(up_state, self.wm.state))

    def on_event(self, event: str) -> None:
        if event == "request_move":
            if self.up_state is not None and self.up_state.is_floating:
                self.wm.enter_overlay(
                    MoveResizeFloatingOverlay(self.wm, self))

    def find_min_w_h(self) -> tuple[float, float]:
        """
        Let overlays know how small we are able to get in i, j, w, h coords
        """
        min_w, _, min_h, _ = self.up_state.size_constraints if self.up_state is not None else (0., 0., 0., 0.)
        min_w *= self.wm.state.size / self.wm.width / self.client_side_scale
        min_h *= self.wm.state.size / self.wm.height / self.client_side_scale

        return min_w, min_h

    def is_focused(self) -> bool:
        return self.up_state is not None and self.up_state.is_focused
