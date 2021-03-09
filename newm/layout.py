import time
import math
import logging
import subprocess
import os
from itertools import product
from threading import Thread

from pywm import (
    PyWM,
    PyWMDownstreamState,
    PYWM_MOD_CTRL,
    PYWM_PRESSED,
    PYWM_MOD_ALT,
    PYWM_MOD_LOGO
)

from pywm.touchpad import (
    TwoFingerSwipePinchGesture,
    HigherSwipeGesture,
    SingleFingerMoveGesture
)

from .state import LayoutState
from .interpolation import LayoutDownstreamInterpolation
from .view import View

from .key_processor import KeyProcessor
from .panel_endpoint import PanelEndpoint
from .sys_backend import SysBackend
from .auth_backend import AuthBackend

from .widget import (
    TopBar,
    BottomBar,
    Background,
    Corner
)
from .overlay import (
    Overlay,
    MoveResizeOverlay,
    MoveResizeFloatingOverlay,
    SwipeOverlay,
    SwipeToZoomOverlay,
    LauncherOverlay,
    OverviewOverlay
)


def _score(i1, j1, w1, h1,
           im, jm,
           i2, j2, w2, h2):

    if (i1, j1, w1, h1) == (i2, j2, w2, h2):
        return 1000

    if im < 0:
        im *= -1
        i1 *= -1
        i2 *= -1
        i1 -= w1
        i2 -= w2
    if jm < 0:
        jm *= -1
        j1 *= -1
        j2 *= -1
        j1 -= h1
        j2 -= h2

    if jm == 1 and im == 0:
        im, jm = jm, im
        i1, j1, w1, h1 = j1, i1, h1, w1
        i2, j2, w2, h2 = j2, i2, h2, w2

    """
    At this point: im == 1, jm == 0
    """
    d_i = i2 - (i1 + w1)
    if d_i < 0:
        return 1000

    d_j = 0
    if j2 > j1 + h1:
        d_j = j2 - (j1 + h1)
    elif j1 > j2 + h2:
        d_j = j1 - (j2 + h2)

    return d_i + d_j


class Animation:
    def __init__(self, layout, reducer, duration, then, overlay_safe=False):
        super().__init__()
        self.layout = layout

        """
        (current state) -> (animation initial state (possibly None), animation final state)
        """
        self.reducer = reducer

        self._initial_state = None
        self._final_state = None
        self._started = None

        # Prevent devision by zero
        self.duration = max(.1, duration)

        self.then = then
        self.overlay_safe = overlay_safe

    def check_finished(self):
        if self._started is not None and self._final_state is None:
            return True

        if self._started is not None and time.time() > self._started + self.duration:
            self.layout.update(self._final_state)
            if callable(self.then):
                self.then()
            return True

        return False

    def start(self):
        try:
            self._initial_state, self._final_state = self.reducer(self.layout.state)
        except:
            """
            An animation may decide it does not want to be executed anymore
            """
            logging.debug("Animation decided not to take place")
            self._initial_state, self._final_state = None, None

        if self._initial_state is not None:
            self.layout.update(self._initial_state)

        self._started = time.time()
        if self._final_state is not None:
            self.layout._animate_to(self._final_state, self.duration)

    def __str__(self):
        return "%s -> %s (%f%s)" % (self._initial_state, self._final_state, self.duration, ", then" if self.then is not None else "")

class LayoutThread(Thread):
    def __init__(self, layout):
        super().__init__()
        self.layout = layout

        """
        Overlay or Animation
        """
        self._pending = []
        self._current_ovr = None
        self._current_anim = None

        self._running = True
        self.start()

    def stop(self):
        self._running = False

    def push(self, nxt):
        if isinstance(nxt, Overlay):
            if self._current_ovr is not None or len([x for x in self._pending if isinstance(x, Overlay)]) > 0:
                logging.debug("Rejecting queued overlay")
                return
            else:
                logging.debug("Queuing overlay")
                self._pending += [nxt]
        else:
            if nxt.overlay_safe:
                logging.debug("Overlay-safe animation not queued")
                self._pending = [nxt] + self._pending
            else:
                logging.debug("Queuing animation")
                self._pending += [nxt]


    def on_overlay_destroyed(self):
        logging.debug("Thread: Finishing overlay...")
        self._current_ovr = None

    def run(self):
        while self._running:
            try:
                if len(self._pending) > 0:
                    if isinstance(self._pending[0], Overlay):
                        if self._current_anim is None and self._current_ovr is None:
                            logging.debug("Thread: Starting overlay...")
                            self._current_ovr = self._pending.pop(0)
                            self.layout.start_overlay(self._current_ovr)
                    else:
                        if self._current_anim is None and (self._current_ovr is None or self._pending[0].overlay_safe):
                            logging.debug("Thread: Starting animation...")
                            self._current_anim = self._pending.pop(0)
                            self._current_anim.start()

                if self._current_anim is not None:
                    if self._current_anim.check_finished():
                        logging.debug("Thread: Finishing animation...")
                        self._current_anim = None

            except Exception:
                logging.exception("Unexpected during LayoutThread")

            time.sleep(1. / 120.)



class Layout(PyWM):
    def __init__(self, mod, **kwargs):
        super().__init__(View, **kwargs)

        self.mod = mod
        self.mod_sym = None
        if mod == PYWM_MOD_ALT:
            self.mod_sym = "Alt"
        elif mod == PYWM_MOD_LOGO:
            self.mod_sym = "Super"
        else:
            raise Exception("Unknown mod")

        self.key_processor = KeyProcessor(self.mod_sym)
        self.key_processor.register_bindings(
            ("M-h", lambda: self.move(-1, 0)),
            ("M-j", lambda: self.move(0, 1)),
            ("M-k", lambda: self.move(0, -1)),
            ("M-l", lambda: self.move(1, 0)),

            ("M-H", lambda: self.move_focused_view(-1, 0)),
            ("M-J", lambda: self.move_focused_view(0, 1)),
            ("M-K", lambda: self.move_focused_view(0, -1)),
            ("M-L", lambda: self.move_focused_view(1, 0)),

            ("M-C-h", lambda: self.resize_focused_view(-1, 0)),
            ("M-C-j", lambda: self.resize_focused_view(0, 1)),
            ("M-C-k", lambda: self.resize_focused_view(0, -1)),
            ("M-C-l", lambda: self.resize_focused_view(1, 0)),

            ("M-Return", lambda: os.system("alacritty &")),
            ("M-c", lambda: os.system("chromium --enable-features=UseOzonePlatform --ozone-platform=wayland &")),  # noqa E501
            ("M-q", lambda: self.close_view()),  # noqa E501

            ("M-p", lambda: self.ensure_locked()),

            ("M-f", lambda: self.toggle_padding()),

            ("M-C", lambda: self.terminate()),
            ("ModPress", lambda: self.enter_overlay(OverviewOverlay(self))),  # noqa E501

        )

        self.sys_backend = SysBackend(self)
        self.sys_backend.register_xf86_keybindings()

        self.auth_backend = AuthBackend(self)

        self.state = None
        self._animation = None

        self.overlay = None

        self.background = None
        self.top_bar = None
        self.bottom_bar = None
        self.corners = []

        self.thread = None
        self.panel_endpoint = None

        self.fullscreen_backup = 0, 0, 1

        self._animations = []

    def reducer(self, state):
        return PyWMDownstreamState(state.lock_perc)

    def process(self):
        if self._animation is not None:
            interpolation, s, d = self._animation
            perc = min((time.time() - s) / d, 1.0)

            if perc >= 0.99:
                self._animation = None

            self.damage()
            return interpolation.get(perc)
        else:
            return self.reducer(self.state)

    def animate(self, old_state, new_state, dt):
        cur = self.reducer(old_state)
        nxt = self.reducer(new_state)

        self._animation = (LayoutDownstreamInterpolation(cur, nxt), time.time(), dt)
        self.damage()


    def main(self):
        logging.debug("Layout main...")

        self.state = LayoutState()

        self.bottom_bar = self.create_widget(BottomBar)
        self.top_bar = self.create_widget(TopBar)

        self.background = None
        if 'wallpaper' in self.config:
            self.background = self.create_widget(Background,
                                                 self.config['wallpaper'])
        self.corners = [
            self.create_widget(Corner, True, True),
            self.create_widget(Corner, True, False),
            self.create_widget(Corner, False, True),
            self.create_widget(Corner, False, False)
        ]

        self.panel_endpoint = PanelEndpoint(self)
        self.thread = LayoutThread(self)

        if 'panel_dir' in self.config:
            logging.debug("Spawning panel...")
            subprocess.Popen(["npm", "run", "start-notifiers"], cwd=self.config['panel_dir'])
            subprocess.Popen(["npm", "run", "start-launcher"], cwd=self.config['panel_dir'])
            subprocess.Popen(["npm", "run", "start-lock"], cwd=self.config['panel_dir'])

        # Initially display cursor
        self.update_cursor()

        # Fade in
        def fade_in():
            time.sleep(.5)
            def reducer(state):
                return None, state.copy(background_opacity=1.)
            self.animate_to(reducer, .5)
        Thread(target=fade_in).start()

        # Greeter
        if self.auth_backend.is_greeter():
            def greet():
                while len([p for p in self.panels() if p.panel == "lock"]) < 1:
                    time.sleep(.5)
                self.ensure_locked()
                self.auth_backend.init_session()
            Thread(target=greet).start()


    def _terminate(self):
        super().terminate()
        if self.top_bar is not None:
            self.top_bar.stop()
        if self.bottom_bar is not None:
            self.bottom_bar.stop()
        if self.panel_endpoint is not None:
            self.panel_endpoint.stop()
        if self.sys_backend is not None:
            self.sys_backend.stop()
        if self.thread is not None:
            self.thread.stop()

    def terminate(self):
        def reducer(state):
            return state.copy(final=True), state.copy(final=True, background_opacity=0.)
        self.animate_to(reducer, .5, self._terminate)


    def _execute_view_main(self, view):
        self.animate_to(view.main, .3, None)


    def animate_to(self, reducer, duration, then=None, overlay_safe=False):
        self.thread.push(Animation(self, reducer, duration, then, overlay_safe))


    def damage(self):
        super().damage()

        for _, v in self._views.items():
            v.damage()

        if self.background is not None:
            self.background.damage()

        if self.top_bar is not None:
            self.top_bar.damage()

        if self.bottom_bar is not None:
            self.bottom_bar.damage()


    def update(self, new_state):
        self.state = new_state
        self.damage()

    def _animate_to(self, new_state, duration):
        self.animate(self.state, new_state, duration)

        for _, v in self._views.items():
            v.animate(self.state, new_state, duration)

        if self.background is not None:
            self.background.animate(self.state, new_state, duration)

        if self.top_bar is not None:
            self.top_bar.animate(self.state, new_state, duration)

        if self.bottom_bar is not None:
            self.bottom_bar.animate(self.state, new_state, duration)



    """
    Utilities
    """

    def windows(self):
        return [v for _, v in self._views.items() if v.is_window()]

    def dialogs(self): 
        return [v for _, v in self._views.items() if v.is_dialog()]

    def panels(self):
        return [v for _, v in self._views.items() if v.is_panel()]

    def find_focused_box(self):
        try:
            view = self.find_focused_view()
            view_state = self.state.get_view_state(view)
            return view_state.i, view_state.j, view_state.w, view_state.h
        except Exception:
            return 0, 0, 1, 1

    def find_focused_view(self):
        for _, view in self._views.items():
            if view.up_state.is_focused:
                return view

        return None

    def place_initial(self, w, h):
        place_i = 0
        place_j = 0
        for j, i in product(range(math.floor(self.state.j),
                                  math.ceil(self.state.j + self.state.size)),
                            range(math.floor(self.state.i),
                                  math.ceil(self.state.i + self.state.size))):
            for jp, ip in product(range(j, j + h), range(i, i + w)):
                if not self.state.is_tile_free(ip, jp):
                    break
            else:
                place_i, place_j = i, j
                break
        else:
            place_i, place_j = self.state.i, self.state.j
            while not self.state.is_tile_free(place_i, place_j):
                place_i += 1

        return place_i, place_j


    """
    Callbacks
    """

    def on_key(self, time_msec, keycode, state, keysyms):
        if self.is_locked():
            return False

        # BEGIN DEBUG
        if self.modifiers & self.mod > 0 and keysyms == "D":
            self.force_close_overlay()
            return True
        # END DEBUG

        if self.overlay is not None and self.overlay.ready():
            logging.debug("...passing to overlay %s", self.overlay)
            if self.overlay.on_key(time_msec, keycode, state, keysyms):
                return True

        return self.key_processor.on_key(state == PYWM_PRESSED,
                                         keysyms,
                                         self.modifiers & self.mod > 0,
                                         self.modifiers & PYWM_MOD_CTRL > 0)

    def on_modifiers(self, modifiers):
        if self.is_locked():
            return False

        logging.debug("Modifiers %d...", modifiers)
        if self.modifiers & self.mod > 0:
            """
            This is a special case, if a SingleFingerMoveGesture has started, then
            Mod is pressed the MoveResize(Floating)Overlay is not triggered - we reallow a
            gesture

            If a gesture has been captured reallow_gesture is a noop
            """
            logging.debug("Resetting gesture")
            self.reallow_gesture()

        if self.overlay is not None and self.overlay.ready():
            logging.debug("...passing to overlay %s", self.overlay)
            if self.overlay.on_modifiers(modifiers):
                return True
        return False

    def on_motion(self, time_msec, delta_x, delta_y):
        if self.is_locked():
            return False

        if self.overlay is not None and self.overlay.ready():
            return self.overlay.on_motion(time_msec, delta_x, delta_y)

        return False

    def on_button(self, time_msec, button, state):
        if self.is_locked():
            return False

        logging.debug("Button...")
        if self.overlay is not None and self.overlay.ready():
            logging.debug("...passing to overlay %s", self.overlay)
            return self.overlay.on_button(time_msec, button, state)

        return False

    def on_axis(self, time_msec, source, orientation, delta, delta_discrete):
        if self.is_locked():
            return False
        
        if self.overlay is not None and self.overlay.ready():
            return self.overlay.on_axis(time_msec, source, orientation,
                                        delta, delta_discrete)

        return False

    def on_gesture(self, gesture):
        if self.is_locked():
            return False

        logging.debug("Gesture %s...", gesture)
        if self.overlay is not None and self.overlay.ready():
            logging.debug("...passing to overlay %s", self.overlay)
            return self.overlay.on_gesture(gesture)
        elif self.overlay is None:
            if self.modifiers & self.mod and \
                    (isinstance(gesture, TwoFingerSwipePinchGesture) or
                     isinstance(gesture, SingleFingerMoveGesture)):
                logging.debug("...MoveResize")
                view = self.find_focused_view()

                if view is not None and view.is_dialog():
                    ovr = MoveResizeFloatingOverlay(self, view)
                    ovr.on_gesture(gesture)
                    self.enter_overlay(ovr)
                    return True

                elif view is not None and view.is_window():
                    ovr = MoveResizeOverlay(self, view)
                    ovr.on_gesture(gesture)
                    self.enter_overlay(ovr)
                    return True

            if isinstance(gesture, HigherSwipeGesture) \
                    and gesture.n_touches == 3:
                logging.debug("...Swipe")
                ovr = SwipeOverlay(self)
                ovr.on_gesture(gesture)
                self.enter_overlay(ovr)
                return True

            if isinstance(gesture, HigherSwipeGesture) \
                    and gesture.n_touches == 4:
                logging.debug("...SwipeToZoom")
                ovr = SwipeToZoomOverlay(self)
                ovr.on_gesture(gesture)
                self.enter_overlay(ovr)
                return True

            if isinstance(gesture, HigherSwipeGesture) \
                    and gesture.n_touches == 5:
                logging.debug("...Launcher")
                ovr = LauncherOverlay(self)
                ovr.on_gesture(gesture)
                self.enter_overlay(ovr)
                return True

            return False


    """
    Actions
    """

    def enter_overlay(self, overlay):
        self.thread.push(overlay)

    def start_overlay(self, overlay):
        logging.debug("Going to enter %s...", overlay)
        self.key_processor.on_other_action()
        self.overlay = overlay
        self.overlay.init()

    # BEGIN DEBUG
    def force_close_overlay(self):
        if self.overlay is None:
            return

        logging.debug("Force-closing %s", self.overlay)
        try:
            self.overlay.destroy()
        finally:
            self.overlay = None
    # END DEBUG

    def ensure_locked(self):
        self.auth_backend.lock()
        lock_screen = [v for v in self.panels() if v.panel == "lock"]
        if len(lock_screen) > 0:
            lock_screen[0].focus()
        else:
            logging.warn("Locking without lock panel - not a good idea")
        def reducer(state):
            return None, state.copy(lock_perc=1., background_opacity=.5)

        self.animate_to(
            reducer,
            .3)

        self._locked = True

    def _trusted_unlock(self):
        if self.is_locked():
            def reducer(state):
                return None, state.copy(lock_perc=0., background_opacity=1.)
            self.animate_to(
                reducer,
                .3,
                lambda: self.update_cursor())

    def exit_overlay(self):
        logging.debug("Going to exit overlay...")
        if self.overlay is None:
            logging.debug("...aborted")
            return

        logging.debug("...destroy")
        self.overlay.destroy()

    def on_overlay_destroyed(self):
        logging.debug("Overlay destroyed")
        self.thread.on_overlay_destroyed()
        self.overlay = None

        logging.debug("Resetting gesture")
        self.reallow_gesture()

    def move(self, delta_i, delta_j):
        i, j, w, h = self.find_focused_box()

        if ((i + w > self.state.i + self.state.size and delta_i > 0) or
                (i < self.state.i and delta_i < 0) or
                (j + h > self.state.j + self.state.size and delta_j > 0) or
                (j < self.state.j and delta_j < 0)):

            vf = self.find_focused_view()
            if vf is not None:
                self.focus_view(vf)
                return


        best_view = None
        best_view_score = 1000

        for k, s in self.state._view_states.items():
            if not s.is_tiled:
                continue

            sc = _score(i, j, w, h, delta_i, delta_j, s.i, s.j, s.w, s.h)
            if sc < best_view_score:
                best_view_score = sc
                best_view = k

        if best_view is not None:
            self.focus_view(self._views[best_view])


    def close_view(self):
        view = [v for _, v in self._views.items() if v.up_state.is_focused]
        if len(view) == 0:
            return

        view = view[0]
        view.close()


    def focus_view(self, view):
        def reducer(state):
            view.focus()
            return None, state.focusing_view(view)
        self.animate_to(reducer, .3)

    def destroy_view(self, view):
        logging.info("Destroying view %s", view)
        state = None
        try:
            state = self.state.get_view_state(view)
        except:
            logging.warn("Unexpected: View %s state not found", view)
            return
        best_view = None
        best_view_score = 1000

        for k, s in self.state._view_states.items():
            if not s.is_tiled:
                continue

            if k == view._handle:
                continue

            sc = (s.i - state.i)**2 + (s.j - state.j**2)
            if sc < best_view_score:
                best_view_score = sc
                best_view = k


        if best_view is not None and best_view in self._views:
            def reducer(state):
                self._views[best_view].focus()
                return None, state\
                    .focusing_view(self._views[best_view])\
                    .without_view_state(view)

            self.animate_to(
                reducer,
                .3)
        else:
            self.animate_to(
                lambda state: (None, state
                    .copy()
                    .without_view_state(view)),
                .3)


    def toggle_padding(self):
        bu = None
        fb = None

        if self.state.padding > 0:
            for _, v in self._views.items():
                if v.is_window():
                    v.set_fullscreen(True)

            self.fullscreen_backup = self.state.i, self.state.j, \
                self.state.size
            fb = self.find_focused_box()
        else:
            for _, v in self._views.items():
                if v.is_window():
                    v.set_fullscreen(False)

            if self.fullscreen_backup:
                bu = self.fullscreen_backup
                self.fullscreen_backup = None


        self.animate_to(
            lambda state: (None, state.with_padding_toggled(
                reset=bu,
                focus_box=fb
            )),
            .3)

    def move_focused_view(self, di, dj):
        def reducer(state):
            view = self.find_focused_view()
            if view is not None:
                try:
                    s = state.get_view_state(view)
                    return (None, state.replacing_view_state(view, i=s.i+di, j=s.j+dj).focusing_view(view))
                except:
                    return (None, state)
            else:
                return (None, state)
        self.animate_to(reducer, .3)

    def resize_focused_view(self, di, dj):
        def reducer(state):
            view = self.find_focused_view()
            if view is not None:
                try:
                    s = state.get_view_state(view)
                    i, j, w, h = s.i, s.j, s.w, s.h
                    w += di
                    h += dj
                    if w == 0:
                        w = 2
                        i -= 1
                    if h == 0:
                        h = 2
                        j -= 1
                    return (None, state.replacing_view_state(view, i=i, j=j, w=w, h=h).focusing_view(view))
                except:
                    return (None, state)
            else:
                return (None, state)
        self.animate_to(reducer, .3)
