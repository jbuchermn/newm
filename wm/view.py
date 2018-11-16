from pywm import PyWMView

from .state import State


class ViewState(State):
    def __init__(self, i, j, w, h):
        super().__init__(['i', 'j', 'w', 'h'])
        self.i = i
        self.j = j
        self.w = w
        self.h = h


class View(PyWMView):
    def __init__(self, wm, handle):
        super().__init__(wm, handle)
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

        self.focus()
        self.wm.place_initial(self)

    def update(self, wm_state, state):
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

    def update_dimensions(self):
        width = round(self.state.w * self.wm.width * self.wm.scale *
                      self.client_side_scale)
        height = round(self.state.h * self.wm.height * self.wm.scale *
                       self.client_side_scale)

        if (width, height) != self.get_dimensions():
            self.set_dimensions(width, height)
