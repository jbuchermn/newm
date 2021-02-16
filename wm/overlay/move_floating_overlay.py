from .overlay import Overlay

class MoveFloatingOverlay(Overlay):
    def __init__(self, layout, view):
        super().__init__(layout)

        self.state = layout.state.get_view_state(view._handle)

    def on_motion(self,time_msec, delta_x, delta_y):
        self.state.i += delta_x * self.layout.state.scale
        self.state.j += delta_y * self.layout.state.scale
        self.layout.damage()

        return False

    def on_button(self, time_msec, button, state):
        self.layout.exit_overlay()
        return True
