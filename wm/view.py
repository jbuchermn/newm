import math
import time

from pywm import PyWMView, PyWMViewDownstreamState

from .interpolation import ViewDownstreamInterpolation
from .move_floating_overlay import MoveFloatingOverlay

PANELS = {
    "newm-panel-notifiers": "notifiers",
    "newm-panel-launcher": "launcher"
}


class ViewState:
    def __init__(self, parent, i, j, w, h):
        self.parent = parent

        self.i = i
        self.j = j
        self.w = w
        self.h = h

    def copy(self):
        return ViewState(self.parent, self.i, self.j, self.w, self.h)

class LauncherPanelState:
    def __init__(self, perc):
        self.perc = perc

    def copy(self):
        return LauncherPanelState(self.perc)


class View(PyWMView):
    def __init__(self, wm, handle):
        super().__init__(wm, handle)

        self.client_side_scale = 1.

        self.state = None

        self.panel = None

        """
        - interpolation
        - next state
        - start time
        - duration
        - then
        """
        self._animation = None

    def is_dialog(self):
        return self.panel is None and self.up_state.is_floating

    def is_window(self):
        return self.panel is None and not self.up_state.is_floating

    def is_panel(self):
        return self.panel is not None

    def main(self):
        print("[Python] New View (%s): %s, %s, %s, xwayland=%s, floating=%s" %
              ("child" if self.parent is not None else "root",
               self.up_state.title, self.app_id, self.role,
               self.is_xwayland, self.up_state.is_floating))

        if self.is_xwayland:
            """
            X clients are responsible to handle HiDPI themselves
            """
            self.client_side_scale = self.wm.config['output_scale']

        if self.app_id in PANELS:
            self.panel = PANELS[self.app_id]
            if self.panel == "launcher":
                self.state = LauncherPanelState(0.0)

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

                ci = self.wm.state.i + self.wm.state.size / 2.
                cj = self.wm.state.j + self.wm.state.size / 2.
                if self.parent is not None:
                    ci = self.parent.state.i + self.parent.state.w / 2.
                    cj = self.parent.state.j + self.parent.state.h / 2.

                w, h = min_w, min_h
                w *= self.wm.state.scale / self.wm.width / self.client_side_scale
                h *= self.wm.state.scale / self.wm.height / self.client_side_scale

                i = ci - w / 2.
                j = cj - h / 2.
                w = w
                h = h

                second_state = ViewState(self.wm.state, i, j, w, h)

            else:
                min_w, _, min_h, _ = self.up_state.size_constraints
                min_w *= self.wm.state.scale / self.wm.width / self.client_side_scale
                min_h *= self.wm.state.scale / self.wm.height / self.client_side_scale

                w = max(math.ceil(min_w), 1)
                h = max(math.ceil(min_h), 1)
                i, j = self.wm.place_initial(self, w, h)

                second_state = ViewState(self.wm.state, i, j, w, h)

            """
            Present
            """
            i, j, w, h = second_state.i, second_state.j, \
                second_state.w, second_state.h

            i += .5*w
            j += .5*h
            w = 0
            h = 0

            self.state = ViewState(self.wm.state, i, j, w, h)

            self.animate_to(second_state, lambda: self.wm.reset_extent(focus_view=self))


    def move(self, delta_x, delta_y):
        if not self.up_state.is_floating:
            return

        self.state.i += delta_x * self.wm.state.scale
        self.state.j += delta_y * self.wm.state.scale
        self.damage()

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
            result.accepts_input = state.perc > 0.0

            result.size = (
                int(self.wm.width * 0.8 * self.client_side_scale),
                int(self.wm.height * 0.8 * self.client_side_scale))

            result.box = (
                self.wm.width * 0.1,
                self.wm.height * 0.1,
                self.wm.width * 0.8,
                self.wm.height * 0.8 if state.perc > 0.0 else 0.0)

        else:
            result.accepts_input = True

            """
            Keep focused view on top
            """
            result.z_index = 2 if self.up_state.is_floating else 0
            if self.up_state.is_focused:
                result.z_index += 1

            """
            Handle client size
            """
            wm_state = state.parent

            width = round(state.w * self.wm.width / wm_state.scale *
                          self.client_side_scale)
            height = round(state.h * self.wm.height / wm_state.scale *
                           self.client_side_scale)

            result.size = (width, height)


            """
            Handle box
            """
            i = state.i
            j = state.j
            w = state.w
            h = state.h

            x = i - wm_state.i + wm_state.padding
            y = j - wm_state.j + wm_state.padding

            w -= 2*wm_state.padding
            h -= 2*wm_state.padding

            x *= self.wm.width / wm_state.size
            y *= self.wm.height / wm_state.size
            w *= self.wm.width / wm_state.size
            h *= self.wm.height / wm_state.size

            if self.up_state.size[0] > 0 and self.up_state.size[1] > 0:
                x -= self.up_state.offset[0] / self.up_state.size[0] * w
                y -= self.up_state.offset[1] / self.up_state.size[1] * h


            if up_state.is_floating:
                """
                Override: Keep floating windows scaled correctly
                """
                w = self.up_state.size[0] * self.client_side_scale
                h = self.up_state.size[1] * self.client_side_scale

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

                width_factor = width / result.size[0] if result.size[0] > 0 else 1.
                height_factor = height / result.size[1] if result.size[1] > 0 else 1.

                if height_factor > width_factor and width_factor >= 1.:
                    w /= height_factor
                elif width_factor > height_factor and height_factor >= 1.:
                    h /= width_factor
                # TODO: Other cases

                result.size = (width, height)


            result.box = (x, y, w, h)

        return result

    def process(self, up_state):
        if self._animation is not None:
            interpolation, nxt_state, s, d, then = self._animation
            perc = min((time.time() - s) / d, 1.0)

            if perc >= 0.99:
                self.state = nxt_state
                self._animation = None
                if then is not None:
                    then()

            self.damage()
            return interpolation.get(perc)
        else:
            return self.reducer(up_state, self.state)

    def animate_to(self, new_state, then=None):
        cur = self.reducer(self.up_state, self.state)
        nxt = self.reducer(self.up_state, new_state)

        self._animation = (ViewDownstreamInterpolation(cur, nxt), new_state, time.time(), .3, then)
        self.damage()



    def on_focus_change(self):
        pass

    def on_event(self, event):
        if event == "request_move":
            if self.up_state.is_floating:
                self.wm.enter_overlay(
                    MoveFloatingOverlay(self.wm, self))

    def destroy(self):
        self.wm.reset_extent()
