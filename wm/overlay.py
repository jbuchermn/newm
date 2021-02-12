from .animate import Transition


class EnterOverlayTransition(Transition):
    def __init__(self, overlay, duration, **new_state):
        super().__init__(overlay.layout, duration, **new_state)
        self.overlay = overlay

    def finish(self):
        self.overlay._enter_finished()
        super().finish()


class ExitOverlayTransition(Transition):
    def __init__(self, overlay, duration, **new_state):
        super().__init__(overlay.layout, duration, **new_state)
        self.overlay = overlay

    def finish(self):
        super().finish()
        self.overlay._exit_finished()


class Overlay:
    def __init__(self, layout):
        self.layout = layout
        self._ready = False

    def ready(self):
        return self._ready

    def init(self):
        transition = self._enter_transition()
        if transition is not None:
            self.layout.animation(transition, pend=True)
        else:
            self._ready = True

    def _enter_finished(self):
        self._ready = True

    def destroy(self):
        self._ready = False
        transition = self._exit_transition()
        if transition is not None:
            self.layout.animation(transition, pend=True)
        else:
            self.layout.on_overlay_destroyed()

    def _exit_finished(self):
        self.layout.on_overlay_destroyed()

    def _enter_transition(self):
        return None

    def _exit_transition(self):
        return None

    def on_key(self, time_msec, keycode, state, keysyms):
        return True

    def on_motion(self, time_msec, delta_x, delta_y):
        return False

    def on_button(self, time_msec, button, state):
        return False

    def on_axis(self, time_msec, source, orientation, delta, delta_discrete):
        return False

    def on_gesture(self, gesture):
        return False

