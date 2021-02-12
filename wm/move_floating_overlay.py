from .overlay import Overlay

class MoveFloatingOverlay(Overlay):
    def __init__(self, layout, view):
        super().__init__(layout)
        self._view = view

    def on_motion(self,time_msec, delta_x, delta_y):
        self._view.move(delta_x, delta_y)

        return False

    def on_button(self, time_msec, button, state):
        self.layout.exit_overlay()
        return True
