from threading import Thread
import time

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
        self.i = 0
        self.j = 0

        try:
            view_state = self.layout.state.get_view_state(view)
            self.i = view_state.i
            self.j = view_state.j

            self.layout.update(
                self.layout.state.replacing_view_state(
                    self.view,
                    move_origin=(self.i, self.j)
                ))
        except Exception:
            print("Could not access view state")

        self.last_dx = 0
        self.last_dy = 0

        self._closed = False

    def reset_gesture(self):
        self.last_dx = 0
        self.last_dy = 0

    def on_gesture(self, values):
        if self._closed:
            return
        
        self.i += 4*(values['delta_x'] - self.last_dx)
        self.j += 4*(values['delta_y'] - self.last_dy)
        self.last_dx = values['delta_x']
        self.last_dy = values['delta_y']
        self.layout.state.update_view_state(self.view, i=self.i, j=self.j)
        self.layout.damage()

    def close(self):
        self._closed = True

        try:
            state = self.layout.state.get_view_state(self.view)
            i, j = state.i, state.j
            fi, fj = round(i), round(j)

            return state.i, state.j, state.w, state.h, fi, fj, state.w, state.h
        except Exception:
            print("Error accessing view state")
            return self.i, self.j, 1, 1, round(self.i), round(self.j), 1, 1


class ResizeOverlay:
    def __init__(self, layout, view):
        self.layout = layout
        self.view = view

        self.i = 0
        self.j = 0
        self.w = 1
        self.h = 1

        try:
            view_state = self.layout.state.get_view_state(view)
            self.i = view_state.i
            self.j = view_state.j
            self.w = view_state.w
            self.h = view_state.h

            self.layout.update(
                self.layout.state.replacing_view_state(
                    self.view,
                    move_origin=(view_state.i, view_state.j),
                    scale_origin=(view_state.w, view_state.h)
                ))
        except Exception:
            print("Could not access view state")

        self._closed = False

    def on_gesture(self, values):
        if self._closed:
            return

        dw = 4*values['delta_x']
        dh = 4*values['delta_y']

        i, j, w, h = self.i, self.j, self.w, self.h

        if self.w + dw < 1:
            d = 1 - (self.w + dw)
            i = self.i - d
            w = 1 + d
        else:
            i = self.i
            w = self.w + dw

        if self.h + dh < 1:
            d = 1 - (self.h + dh)
            j = self.j - d
            h = 1 + d
        else:
            j = self.j
            h = self.h + dh

        self.layout.state.update_view_state(self.view, i=i, j=j, w=w, h=h)

        self.layout.damage()

    def close(self):
        self._closed = True

        try:
            state = self.layout.state.get_view_state(self.view)
            i, j, w, h = state.i, state.j, state.w, state.h
            fi, fj = round(i), round(j)
            fw, fh = round(w), round(h)
            fw = max(1, fw)
            fh = max(1, fh)

            return state.i, state.j, state.w, state.h, fi, fj, fw, fh
        except Exception:
            print("Error accessing view state")
            return self.i, self.j, self.w, self.h, self.i, self.j, self.w, self.h



class MoveResizeOverlay(Overlay, Thread):
    def __init__(self, layout):
        Overlay.__init__(self, layout)
        Thread.__init__(self)

        self.layout.update_cursor(False)

        self.view = self.layout.find_focused_view()

        self.overlay = None

        """
        If move has been finished and we are animating towards final position
            (view initial i, view initial j, view final i, view final j, initial time, finished time)
        """
        self._target_view_pos = None

        """
        If resize has been finished and we are animating towards final size
            (view initial w, view initial h, view final w, view final h, initial time, finished time)
        """
        self._target_view_size = None

        """
        If we are adjusting viewpoint (after gesture finished or during)
            (layout initial i, layout initial j, layout final i, layout final j, initial time, finished time)
        """
        self._target_layout_pos = None
        
        self._running = True
        self._wants_close = False

    def post_init(self):
        self.start()

    def run(self):
        while self._running:
            t = time.time()

            in_prog = False
            if self._target_view_pos is not None:
                in_prog = True
                ii, ij, fi, fj, it, ft = self._target_view_pos
                if t > ft:
                    self.layout.state.update_view_state(self.view, i=fi, j=fj)
                    self._target_view_pos = None
                else:
                    perc = (t-it)/(ft-it)
                    self.layout.state.update_view_state(self.view, i=ii + perc*(fi-ii), j=ij + perc*(fj-ij))
                self.layout.damage()


            if self._target_view_size is not None:
                in_prog = True
                iw, ih, fw, fh, it, ft = self._target_view_size
                if t > ft:
                    self.layout.state.update_view_state(self.view, w=fw, h=fh, scale_origin=(None, None))
                    self._target_view_size = None
                else:
                    perc = (t-it)/(ft-it)
                    self.layout.state.update_view_state(self.view, w=iw + perc*(fw-iw), h=ih + perc*(fh-ih))
                self.layout.damage()

            if self._target_layout_pos is not None:
                in_prog = True
                ii, ij, fi, fj, it, ft = self._target_layout_pos
                if t > ft:
                    self.layout.state.i = fi
                    self.layout.state.j = fj
                    self._target_layout_pos = None
                else:
                    perc = (t-it)/(ft-it)
                    self.layout.state.i=ii + perc*(fi-ii)
                    self.layout.state.j=ij + perc*(fj-ij)
                self.layout.damage()

            elif self.overlay is not None:
                try:
                    view_state = self.layout.state.get_view_state(self.view)
                    i, j, w, h = view_state.i, view_state.j, view_state.w, view_state.h
                    i, j, w, h = round(i), round(j), round(w), round(h)

                    fi, fj = self.layout.state.i, self.layout.state.j

                    if i + w > fi + self.layout.state.size:
                        fi = i + w - self.layout.state.size

                    if j + h > fj + self.layout.state.size:
                        fj = j + h - self.layout.state.size

                    if i < fi:
                        fi = i

                    if j < fj:
                        fj = j

                    if i != self.layout.state.i or j != self.layout.state.j:
                        self._target_layout_pos = (self.layout.state.i, self.layout.state.j, fi, fj, time.time(), time.time() + .3)

                except Exception:
                    print("Cannot read view state")


            if not in_prog and self._wants_close:
                self._running = False

            time.sleep(1. / 120.)

        self.layout.exit_overlay()

    def on_gesture(self, gesture):
        if not self._running or self._wants_close:
            return

        if isinstance(gesture, TwoFingerSwipePinchGesture):
            if self._target_view_size is not None:
                return

            self.overlay = ResizeOverlay(self.layout, self.view)
            LowpassGesture(gesture).listener(GestureListener(
                self.overlay.on_gesture,
                self.finish
            ))
            return True

        if isinstance(gesture, SingleFingerMoveGesture):
            if self._target_view_pos is not None:
                return

            self.overlay = MoveOverlay(self.layout, self.view)
            LowpassGesture(gesture).listener(GestureListener(
                self.overlay.on_gesture,
                self.finish
            ))
            return True

        return False


    def finish(self):
        if self.overlay is not None:
            ii, ij, iw, ih, fi, fj, fw, fh = self.overlay.close()
            self.overlay = None

            if ii != fi or ij != fj:
                self._target_view_pos = (ii, ij, fi, fj, time.time(), time.time() + .3)
            if iw != fw or iw != fw:
                self._target_view_size = (iw, ih, fw, fh, time.time(), time.time() + .3)


        if not self.layout.modifiers & self.layout.mod:
            self.close()

    def on_motion(self, time_msec, delta_x, delta_y):
        return False

    def on_axis(self, time_msec, source, orientation, delta, delta_discrete):
        return False

    def on_key(self, time_msec, keycode, state, keysyms):
        if state != PYWM_PRESSED and self.layout.mod_sym in keysyms:
            if self.overlay is None:
                self.close()

    def on_modifiers(self, modifiers):
        return False

    def close(self):
        if self.overlay is not None:
            self.overlay.close()
        self._wants_close = True

    def pre_destroy(self):
        self._running = False

    def _exit_transition(self):
        self.layout.update_cursor(True)
        try:
            # Clean up any possible mishaps - should not be necessary
            view_state = self.layout.state.get_view_state(self.view)
            i = round(view_state.i)
            j = round(view_state.j)
            w = round(view_state.w)
            h = round(view_state.h)

            return self.layout.state.replacing_view_state(
                self.view,
                i=i, j=j, w=w, h=h,
                scale_origin=(None, None), move_origin=(None, None)), .3
        except Exception:
            return None, 0
