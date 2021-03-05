import math
import time
import logging

from pywm import PyWMView, PyWMViewDownstreamState

from .interpolation import ViewDownstreamInterpolation
from .overlay import MoveResizeFloatingOverlay

PANELS = {
    "newm-panel-notifiers": "notifiers",
    "newm-panel-launcher": "launcher",
    "newm-panel-lock": "lock"
}

CORNER_RADIUS = 12.5


class View(PyWMView):
    def __init__(self, wm, handle):
        super().__init__(wm, handle)

        self.client_side_scale = 1.

        self.panel = None

        """
        - interpolation
        - start time
        - duration
        """
        self._animation = None

    def __str__(self):
        return "View (%d)" % self._handle

    def is_dialog(self):
        return self.panel is None and self.up_state.is_floating

    def is_window(self):
        return self.panel is None and not self.up_state.is_floating

    def is_panel(self):
        return self.panel is not None

    def main(self, state):
        logging.info(
            "Init: %s (%s): %s, %s, %s, xwayland=%s, floating=%s",
            self, "child" if self.parent is not None else "root",
            self.up_state.title, self.app_id, self.role,
            self.is_xwayland, self.up_state.is_floating)

        try:
            if self.wm.config['xwayland_handle_scale_clientside']:
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
                    self.client_side_scale = self.wm.config['output_scale'] if 'output_scale' in self.wm.config else 1.
        except:
            pass

        if isinstance(self.app_id, str) and self.app_id in PANELS:
            self.panel = PANELS[self.app_id]
            logging.debug("Registered panel %s: %s", self.app_id, self.panel)

        else:
            second_state = None

            """
            Place initially
            """
            if self.up_state.is_floating:
                min_w, _, min_h, _ = self.up_state.size_constraints

                if (min_w, min_h) == (0, 0):
                    (min_w, min_h) = self.up_state.size

                if min_w == 0 or min_h == 0:
                    return

                ci = state.i + state.size / 2.
                cj = state.j + state.size / 2.
                if self.parent is not None:
                    try:
                        ci = state.get_view_state(self.parent).i + state.get_view_state(self.parent).w / 2.
                        cj = state.get_view_state(self.parent).j + state.get_view_state(self.parent).h / 2.
                    except:
                        logging.warn("Unexpected: Could not access parent %s state" % self.parent)

                w, h = min_w, min_h
                w *= state.scale / self.wm.width / self.client_side_scale
                h *= state.scale / self.wm.height / self.client_side_scale

                i = ci - w / 2.
                j = cj - h / 2.
                w = w
                h = h

                second_state = (i, j, w, h)

            else:
                min_w, _, min_h, _ = self.up_state.size_constraints
                min_w *= state.scale / self.wm.width / self.client_side_scale
                min_h *= state.scale / self.wm.height / self.client_side_scale

                w = max(math.ceil(min_w), 1)
                h = max(math.ceil(min_h), 1)
                i, j = self.wm.place_initial(w, h)

                second_state = (i, j, w, h)

            """
            Present
            """
            i, j, w, h = second_state
            i1, j1, w1, h1 = second_state

            i += .5*w
            j += .5*h
            w = 0
            h = 0

            self.focus()

            state1 = state.with_view_state(
                    self,
                    is_tiled=not self.up_state.is_floating, i=i, j=j, w=w, h=h)


            state2 = state1.replacing_view_state(
                    self, i=i1, j=j1, w=w1, h=h1
                ).focusing_view(
                    self
                )

            return state1, state2

    def destroy(self):
        self.wm.destroy_view(self)

    def reducer(self, up_state, state):
        result = PyWMViewDownstreamState()

        if self.panel == "notifiers":
            result.z_index = 6
            result.accepts_input = False

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
            result.accepts_input = state.launcher_perc > 0.0

            result.size = (
                int(self.wm.width * 0.8 * self.client_side_scale),
                int(self.wm.height * 0.8 * self.client_side_scale))

            result.box = (
                self.wm.width * 0.1,
                self.wm.height * 0.1 + (1. - state.launcher_perc) * self.wm.height,
                self.wm.width * 0.8,
                self.wm.height * 0.8)


        elif self.panel == "lock":
            result.z_index = 100
            result.accepts_input = state.lock_perc > 0.0
            result.lock_enabled = True

            result.size = (
                int(self.wm.width * self.client_side_scale),
                int(self.wm.height * self.client_side_scale))

            result.box = (
                0,
                (1. - state.lock_perc) * self.wm.height,
                self.wm.width,
                self.wm.height)


        else:
            result.accepts_input = True
            result.corner_radius = CORNER_RADIUS if self.parent is None else 0

            """
            Keep focused view on top
            """
            result.z_index = 2 if self.up_state.is_floating else 0
            if self.up_state.is_focused:
                result.z_index += 1


            self_state = None
            try:
                self_state = state.get_view_state(self)
            except Exception:
                """
                This can happen, if main has not been executed yet
                (e.g. during an overlay) - just return a box not displayed
                """
                logging.debug("Could not access view %s state" % self)
                return result

            """
            Handle client size
            """

            w_for_size, h_for_size = self_state.scale_origin
            if w_for_size is None:
                w_for_size, h_for_size = self_state.w, self_state.h
            width = round(w_for_size * self.wm.width / state.scale *
                          self.client_side_scale)
            height = round(h_for_size * self.wm.height / state.scale *
                           self.client_side_scale)

            result.size = (width, height)


            """
            Handle box
            """
            i = self_state.i
            j = self_state.j
            w = self_state.w
            h = self_state.h

            x = i - state.i + state.padding
            y = j - state.j + state.padding / (self.wm.height / self.wm.width)

            w -= 2*state.padding
            h -= 2*state.padding / (self.wm.height / self.wm.width)

            x *= self.wm.width / state.size
            y *= self.wm.height / state.size
            w *= self.wm.width / state.size
            h *= self.wm.height / state.size

            if self.up_state.size[0] > 0 and self.up_state.size[1] > 0:
                x -= self.up_state.offset[0] / self.up_state.size[0] * w
                y -= self.up_state.offset[1] / self.up_state.size[1] * h


            if up_state.is_floating:
                """
                Override: Keep floating windows scaled correctly
                """
                w = self.up_state.size[0] / self.client_side_scale * (state.scale / state.size)
                h = self.up_state.size[1] / self.client_side_scale * (state.scale / state.size)

            else:
                """
                Override: Keep aspect-ratio of windows
                """
                min_w, max_w, min_h, max_h = self.up_state.size_constraints
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

        result.opacity = state.background_opacity
        return result

    def process(self, up_state):
        if self._animation is not None:
            interpolation, s, d = self._animation
            perc = min((time.time() - s) / d, 1.0)

            if perc >= 0.99:
                self._animation = None

            self.damage()
            return interpolation.get(perc)
        else:
            return self.reducer(up_state, self.wm.state)

    def animate(self, old_state, new_state, dt):
        cur = self.reducer(self.up_state, old_state)
        nxt = self.reducer(self.up_state, new_state)

        self._animation = (ViewDownstreamInterpolation(cur, nxt), time.time(), dt)
        self.damage()

    def on_event(self, event):
        if event == "request_move":
            if self.up_state.is_floating:
                self.wm.enter_overlay(
                    MoveResizeFloatingOverlay(self.wm, self))

    def find_min_w_h(self):
        """
        Let overlays know how small we are able to get in i, j, w, h coords
        """
        min_w, _, min_h, _ = self.up_state.size_constraints
        min_w *= self.wm.state.scale / self.wm.width / self.client_side_scale
        min_h *= self.wm.state.scale / self.wm.height / self.client_side_scale

        return min_w, min_h
