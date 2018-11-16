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
        _, _, _, xwayland = self.get_info()
        if xwayland:
            """
            X cleints are responsible to handle
            HiDPI themselves
            """
            self.client_side_scale = self.wm.config['output_scale']

        self.wm.place_initial(self)

    def update(self, state, wm_state=None):
        if wm_state is None:
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

    def update_dimensions(self, state=None):
        if state is None:
            state = self.state

        width = round(state.w * self.wm.width / self.wm.scale *
                      self.client_side_scale)
        height = round(state.h * self.wm.height / self.wm.scale *
                       self.client_side_scale)

        if (width, height) != self.get_dimensions():
            self.set_dimensions(width, height)
