import math

from pywm import PyWMView

from .state import State
from .animate import Animate, Transition
from .move_floating_overlay import MoveFloatingOverlay

PANELS = {
    "newm-panel-notifiers": "notifiers",
    "newm-panel-launcher": "launcher"
}


class ViewState(State):
    def __init__(self, i, j, w, h):
        super().__init__(['i', 'j', 'w', 'h'])
        self.i = i
        self.j = j
        self.w = w
        self.h = h


class PresentViewTransition(Transition):
    def __init__(self, layout, view, duration, i, j, w, h):
        super().__init__(view, duration, ease=True)
        self.layout = layout
        self.view = view
        self.i = i
        self.j = j
        self.w = w
        self.h = h

    def setup(self):
        new_state = self.view.state.copy()
        new_state.i = self.i
        new_state.j = self.j
        new_state.w = self.w
        new_state.h = self.h
        super().setup(new_state)

    def finish(self):
        self.layout.reset_extent(focus_view=self.view)


class View(PyWMView, Animate):
    def __init__(self, wm, handle):
        PyWMView.__init__(self, wm, handle)
        Animate.__init__(self)
        self.state = ViewState(0, 0, 0, 0)
        self.client_side_scale = 1.

        self.in_progress = False
        self.panel = None

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
            self.set_accepts_input(False)
            self.set_z_index(6)

        else:
            self.set_accepts_input(True)
            self.set_z_index(0)

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
                w *= self.wm.scale / self.wm.width / self.client_side_scale
                h *= self.wm.scale / self.wm.height / self.client_side_scale

                self.state.i = ci - w / 2.
                self.state.j = cj - h / 2.
                self.state.w = w
                self.state.h = h

            else:
                min_w, _, min_h, _ = self.up_state.size_constraints
                min_w *= self.wm.scale / self.wm.width / self.client_side_scale
                min_h *= self.wm.scale / self.wm.height / self.client_side_scale

                print(self.up_state.size_constraints, self.up_state.size)

                self.wm.place_initial(self, max(math.ceil(min_w), 1),
                                      max(math.ceil(min_h), 1))

            """
            Present
            """
            i, j, w, h = self.state.i, self.state.j, self.state.w, self.state.h
            self.state.w = 0
            self.state.h = 0

            self.state.i += .5*w
            self.state.j += .5*h

            self.animation(PresentViewTransition(self.wm, self, .5, i, j, w, h))

    def move(self, delta_x, delta_y):
        if not self.up_state.is_floating:
            return

        self.state.i += delta_x * self.wm.scale
        self.state.j += delta_y * self.wm.scale

        self.update()

    def process(self, last_down_state, up_state):
        if self.panel == "notifiers":
            self.set_size(
                self.wm.width * 0.2 * self.client_side_scale,
                self.wm.height * 0.3 * self.client_side_scale)

            self.set_box(
                self.wm.width * 0.4,
                self.wm.height * 0.7,
                self.wm.width * 0.2,
                self.wm.height * 0.3)

        elif self.panel == "launcher":
            self.set_size(
                self.wm.width * 0.8 * self.client_side_scale,
                self.wm.height * 0.8 * self.client_side_scale)

            self.set_box(
                self.wm.width * 0.1,
                self.wm.height * 0.1,
                self.wm.width * 0.8,
                0)

        else:
            """
            Keep focused view on top
            """
            if self.up_state.is_focused:
                self.set_z_index(1 + (2 if self.up_state.is_floating else 0))
            else:
                self.set_z_index(0 + (2 if self.up_state.is_floating else 0))

            """
            Handle client size
            """
            state = self.state
            wm_state = self.wm.state

            width = round(state.w * self.wm.width / self.wm.scale *
                          self.client_side_scale)
            height = round(state.h * self.wm.height / self.wm.scale *
                           self.client_side_scale)

            if not self.in_progress:
                min_w, max_w, min_h, max_h = self.up_state.size_constraints
                if width < min_w and min_w > 0:
                    print("Warning: Width: %d !> %d" % (width, min_w))
                if width > max_w and max_w > 0:
                    print("Warning: Width: %d !< %d" % (width, max_w))
                if height < min_h and min_h > 0:
                    print("Warning: Height: %d !> %d" % (height, min_h))
                if height > max_h and max_h > 0:
                    print("Warning: Height: %d !< %d" % (height, max_h))

                if (width, height) != self.up_state.size:
                    print("Setting", (width, height))
                    self.set_size(width, height)


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


            """
            Override: Keep floating windows scaled correctly
            """
            if self.up_state.is_floating and not self.in_progress:
                w = self.up_state.size[0] * self.client_side_scale
                h = self.up_state.size[1] * self.client_side_scale

            self.set_box(x, y, w, h)


    def update(self, finished=False):
        self.in_progress = not finished
        self.process(self.last_down_state, self.up_state)

    def on_focus_change(self):
        pass

    def on_event(self, event):
        if event == "request_move":
            if self.up_state.is_floating:
                self.wm.enter_overlay(
                    MoveFloatingOverlay(self.wm, self))

    def destroy(self):
        self.wm.reset_extent()
