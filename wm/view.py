import math

from pywm import PyWMView

from .state import State
from .animate import Animate


class ViewState(State):
    def __init__(self, i, j, w, h):
        super().__init__(['i', 'j', 'w', 'h'])
        self.i = i
        self.j = j
        self.w = w
        self.h = h


class View(PyWMView, Animate):
    def __init__(self, wm, handle):
        PyWMView.__init__(self, wm, handle)
        Animate.__init__(self)
        self.state = ViewState(0, 0, 0, 0)

    def main(self):
        self.client_side_scale = 1.
        t1, t2, t3, xwayland = self.get_info()
        print("[Python] New View: %s, %s, %s, %s" % (t1, t2, t3, xwayland))
        if xwayland:
            """
            X cleints are responsible to handle
            HiDPI themselves
            """
            self.client_side_scale = self.wm.config['output_scale']

        min_w, _, min_h, _ = self.get_size_constraints()
        if self.floating:
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
            self.update()
        else:
            min_w *= self.wm.scale / self.wm.width / self.client_side_scale
            min_h *= self.wm.scale / self.wm.height / self.client_side_scale

            self.wm.place_initial(self, max(math.ceil(min_w), 1),
                                  max(math.ceil(min_h), 1))

    def update(self):
        state = self.state
        wm_state = self.wm.state

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

        self.set_box(x, y, w, h)

    def update_size(self):
        state = self.state

        width = round(state.w * self.wm.width / self.wm.scale *
                      self.client_side_scale)
        height = round(state.h * self.wm.height / self.wm.scale *
                       self.client_side_scale)

        min_w, max_w, min_h, max_h = self.get_size_constraints()
        if width < min_w and min_w > 0:
            print("Warning: Width: %d !> %d" % (width, min_w))
        if width > max_w and max_w > 0:
            print("Warning: Width: %d !< %d" % (width, max_w))
        if height < min_h and min_h > 0:
            print("Warning: Height: %d !> %d" % (height, min_h))
        if height > max_h and max_h > 0:
            print("Warning: Height: %d !< %d" % (height, max_h))

        if (width, height) != self.get_size():
            self.set_size(width, height)

    def destroy(self):
        self.wm.reset_extent()
