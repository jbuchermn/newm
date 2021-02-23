import logging

class Overlay:
    def __init__(self, layout):
        self.layout = layout
        self._ready = False

    def ready(self):
        return self._ready

    def init(self):
        wm_state, dt = self._enter_transition()
        if wm_state is not None:
            logging.debug("Overlay: Enter animation")
            self.layout.animate_to(lambda _: (None, wm_state), dt, self._enter_finished, overlay_safe=True)
        else:
            self._ready = True

        self.post_init()

    def _enter_finished(self):
        logging.debug("Overlay: Enter animation completed")
        self._ready = True

    def destroy(self):
        self.pre_destroy()

        self._ready = False
        wm_state, dt = self._exit_transition()
        if wm_state is not None:
            logging.debug("Overlay: Exit animation")
            self.layout.animate_to(lambda _: (None, wm_state), dt, self._exit_finished, overlay_safe=True)
        else:
            self.layout.on_overlay_destroyed()

    def _exit_finished(self):
        logging.debug("Overlay: Exit animation completed")
        self.layout.on_overlay_destroyed()


    """
    Virtual methods
    """

    def post_init(self):
        pass

    def pre_destroy(self):
        pass
    
    def _enter_transition(self):
        return None, 0

    def _exit_transition(self):
        return None, 0

    def on_key(self, time_msec, keycode, state, keysyms):
        return True

    def on_modifiers(self, modifiers):
        return False

    def on_motion(self, time_msec, delta_x, delta_y):
        return False

    def on_button(self, time_msec, button, state):
        return False

    def on_axis(self, time_msec, source, orientation, delta, delta_discrete):
        return False

    def on_gesture(self, gesture):
        return False

