from pywm import PYWM_PRESSED

from pywm.touchpad import (
    SingleFingerMoveGesture,
    TwoFingerSwipePinchGesture,
    GestureListener,
    LowpassGesture
)
from .overlay import Overlay

class MoveOverlay:
    def __init__(self, layout, view):
        self.layout = layout

        self.view = view
        self.original_state = self.layout.state.copy()


        view_state = self.original_state.get_view_state(view._handle)

        self.layout.update(
            self.original_state.copy().replacing_view_state(
                self.view._handle,
                move_origin=(view_state.i, view_state.j)
            ))

        self.last_dx = 0
        self.last_dy = 0
        
        self._closed = False

    def reset_gesture(self):
        self.last_dx = 0
        self.last_dy = 0

    def on_gesture(self, values):
        if self._closed:
            return
        
        self.layout.state.get_view_state(self.view._handle).i += 4*(values['delta_x'] - self.last_dx)
        self.layout.state.get_view_state(self.view._handle).j += 4*(values['delta_y'] - self.last_dy)
        self.last_dx = values['delta_x']
        self.last_dy = values['delta_y']
        self.layout.damage()

    def close(self):
        self._closed = True

        state = self.layout.state.get_view_state(self.view._handle)
        i, j = state.i, state.j
        fi, fj = round(i), round(j)

        return self.original_state.replacing_view_state(self.view._handle, i=fi, j=fj, move_origin=(None, None))


class ResizeOverlay:
    def __init__(self, layout, view):
        self.layout = layout

        self.view = view
        self.original_state = self.layout.state.copy()

        view_state = self.original_state.get_view_state(view._handle)

        self.layout.update(
            self.original_state.copy().replacing_view_state(
                self.view._handle,
                scale_origin=(view_state.w, view_state.h)
            ))

        self.last_dx = 0
        self.last_dy = 0

        self._closed = False

    def reset_gesture(self):
        self.last_dx = 0
        self.last_dy = 0

    def on_gesture(self, values):
        if self._closed:
            return

        self.layout.state.get_view_state(self.view._handle).w += 4*(values['delta_x'] - self.last_dx)
        self.layout.state.get_view_state(self.view._handle).h += 4*(values['delta_y'] - self.last_dy)
        self.last_dx = values['delta_x']
        self.last_dy = values['delta_y']
        self.layout.damage()

    def close(self):
        self._closed = True

        state = self.layout.state.get_view_state(self.view._handle)
        w, h = state.w, state.h
        fw, fh = round(w), round(h)
        fw = max(1, fw)
        fh = max(1, fh)

        """
        TODO: Momentum
        """

        return self.original_state.replacing_view_state(self.view._handle, w=fw, h=fh, scale_origin=(None, None))


class MoveResizeOverlay(Overlay):
    def __init__(self, layout):
        super().__init__(self)

        self.layout = layout
        self.layout.update_cursor(False)

        self.view = self.layout.find_focused_view()

        self.overlay = None
        self._exit_transition_ret = None
        self._anim_block = False

    def on_gesture(self, gesture):
        if self._anim_block:
            return True

        if isinstance(gesture, TwoFingerSwipePinchGesture):
            self.overlay = ResizeOverlay(self.layout, self.view)
            LowpassGesture(gesture).listener(GestureListener(
                self.overlay.on_gesture,
                self.finish
            ))
            return True

        if isinstance(gesture, SingleFingerMoveGesture):
            self.overlay = MoveOverlay(self.layout, self.view)
            LowpassGesture(gesture).listener(GestureListener(
                self.overlay.on_gesture,
                self.finish
            ))
            return True

        return False


    def finish(self):
        if self.overlay is not None:
            self._exit_transition_ret = self.overlay.close()

        if not self.layout.modifiers & self.layout.mod:
            self.layout.exit_overlay()
        else:
            self._anim_block = True
            def ready():
                self._anim_block = False
            self.layout.animate_to(
                self._exit_transition_ret, .3,
                then=ready)
            self.overlay = None
            self._exit_transition_ret = None

    def on_motion(self, time_msec, delta_x, delta_y):
        return False

    def on_axis(self, time_msec, source, orientation, delta, delta_discrete):
        return False

    def on_key(self, time_msec, keycode, state, keysyms):
        if state != PYWM_PRESSED and self.layout.mod_sym in keysyms:
            if self.overlay is not None:
                # if self._exit_transition_ret is None:
                #     self._exit_transition_ret = self.overlay.close()
                # self.layout.exit_overlay()
                pass
            else:
                self.layout.exit_overlay()

    def on_modifiers(self, modifiers):
        return False

    def _exit_transition(self):
        self.layout.update_cursor(True)
        return self._exit_transition_ret, .3
