from .overlay import Overlay

class MoveFloatingOverlay(Overlay):
    def __init__(self, layout, view):
        super().__init__(layout)

        self.view = view
        self.i = 0
        self.j = 0
        try:
            state = self.layout.state.get_view_state(self.view)
            self.i = state.i
            self.j = state.j
        except Exception:
            print("Error accessing view state: %s" % view)

    def on_motion(self, time_msec, delta_x, delta_y):
        self.i += delta_x * self.layout.state.scale
        self.j += delta_y * self.layout.state.scale

        self.layout.state.update_view_state(self.view, i=self.i, j=self.j)
        self.layout.damage()

        return False

    def on_button(self, time_msec, button, state):
        self.layout.exit_overlay()
        return True
