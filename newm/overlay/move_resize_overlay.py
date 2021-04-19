from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from threading import Thread
import time
import logging

from pywm import PYWM_PRESSED

from pywm.touchpad import (
    SingleFingerMoveGesture,
    TwoFingerSwipePinchGesture,
    GestureListener,
    LowpassGesture
)
from pywm.touchpad.gestures import Gesture
from .overlay import Overlay
from ..grid import Grid
from ..hysteresis import Hysteresis
from ..config import configured_value

if TYPE_CHECKING:
    from ..layout import Layout
    from ..view import View
    from ..state import LayoutState

logger = logging.getLogger(__name__)

conf_move_grid_ovr = configured_value("move.grid_ovr", 0.2)
conf_move_grid_m = configured_value("move.grid_m", 2)
conf_resize_grid_ovr = configured_value("resize.grid_ovr", 0.1)
conf_resize_grid_m = configured_value("resize.grid_m", 3)
conf_hyst = configured_value("resize.hyst", 0.2)
conf_gesture_factor = configured_value("move_resize.gesture_factor", 4)
conf_anim_t = configured_value("anim_time", .3)

class _Overlay:
    def reset_gesture(self) -> None:
        pass

    def on_gesture(self, values: dict[str, float]) -> None:
        pass

    def close(self) -> tuple[float, float, float, float, float, float, float, float, float]:
        pass


class MoveOverlay(_Overlay):
    def __init__(self, layout: Layout, view: View) -> None:
        self.layout = layout

        self.view = view
        self.i = 0.
        self.j = 0.

        try:
            view_state = self.layout.state.get_view_state(self.view)
            self.i = view_state.i
            self.j = view_state.j

            self.layout.update(
                self.layout.state.replacing_view_state(
                    self.view,
                    move_origin=(self.i, self.j)
                ))
        except Exception:
            logger.warn("Unexpected: Could not access view %s state", self.view)

        self.i_grid = Grid("i", round(self.i - 3), round(self.i + 3), self.i, conf_move_grid_ovr(), conf_move_grid_m())
        self.j_grid = Grid("j", round(self.j - 3), round(self.j + 3), self.j, conf_move_grid_ovr(), conf_move_grid_m())

        self.last_dx = 0.
        self.last_dy = 0.

        self._closed = False

    def reset_gesture(self) -> None:
        self.last_dx = 0
        self.last_dy = 0

    def on_gesture(self, values: dict[str, float]) -> None:
        if self._closed:
            return
        
        self.i += conf_gesture_factor()*(values['delta_x'] - self.last_dx)
        self.j += conf_gesture_factor()*(values['delta_y'] - self.last_dy)
        self.last_dx = values['delta_x']
        self.last_dy = values['delta_y']
        self.layout.state.update_view_state(
            self.view, i=self.i_grid.at(self.i), j=self.j_grid.at(self.j))
        self.layout.damage()

    def close(self) -> tuple[float, float, float, float, float, float, float, float, float]:
        self._closed = True

        try:
            state = self.layout.state.get_view_state(self.view)
            fi, ti = self.i_grid.final()
            fj, tj = self.j_grid.final()

            logger.debug("Move - Grid finals: %f %f (%f %f)", fi, fj, ti, tj)

            return state.i, state.j, state.w, state.h, fi, fj, state.w, state.h, max(ti, tj)
        except Exception:
            logger.warn("Unexpected: Could not access view %s state... returning default placement", self.view)
            return self.i, self.j, 1, 1, round(self.i), round(self.j), 1, 1, 1


class ResizeOverlay(_Overlay):
    def __init__(self, layout: Layout, view: View):
        self.layout = layout
        self.view = view

        self.i = 0.
        self.j = 0.
        self.w = 1.
        self.h = 1.

        self.hyst_w = lambda v: v
        self.hyst_h = lambda v: v

        try:
            view_state = self.layout.state.get_view_state(self.view)
            self.i = view_state.i
            self.j = view_state.j
            self.w = view_state.w
            self.h = view_state.h

            self.hyst_w = Hysteresis(conf_hyst(), self.w)
            self.hyst_h = Hysteresis(conf_hyst(), self.h)

            self.layout.update(
                self.layout.state.replacing_view_state(
                    self.view,
                    move_origin=(self.i, self.j),
                    scale_origin=(self.w, self.h)
                ))
        except Exception:
            logger.warn("Unexpected: Could not access view %s state", self.view)


        self.i_grid = Grid("i", round(self.i - 3), round(self.i + 3), self.i, conf_move_grid_ovr(), conf_move_grid_m())
        self.j_grid = Grid("j", round(self.j - 3), round(self.j + 3), self.j, conf_move_grid_ovr(), conf_move_grid_m())
        self.w_grid = Grid("w", 1, round(self.w + 3), self.w, conf_resize_grid_ovr(), conf_resize_grid_m())
        self.h_grid = Grid("h", 1, round(self.h + 3), self.h, conf_resize_grid_ovr(), conf_resize_grid_m())

        self._closed = False

    def on_gesture(self, values: dict[str, float]) -> None:
        if self._closed:
            return

        dw = conf_gesture_factor()*values['delta_x']
        dh = conf_gesture_factor()*values['delta_y']

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

        w_ = self.w_grid.at(w)
        h_ = self.h_grid.at(h)
        self.layout.state.update_view_state(
            self.view, i=self.i_grid.at(i), j=self.j_grid.at(j),
            w=w_, h=h_,
            scale_origin=(self.hyst_w(w_),self.hyst_h(h_))
        )

        self.layout.damage()


    def close(self) -> tuple[float, float, float, float, float, float, float, float, float]:
        self._closed = True

        try:
            state = self.layout.state.get_view_state(self.view)
            fi, ti = self.i_grid.final()
            fj, tj = self.j_grid.final()
            fw, tw = self.w_grid.final()
            fh, th = self.h_grid.final()

            logger.debug("Resize - Grid finals: %f %f %f %f (%f %f %f %f)", fi, fj, fw, fh, ti, tj, tw, th)

            return state.i, state.j, state.w, state.h, fi, fj, fw, fh, max(ti, tj, tw, th)
        except Exception:
            logger.warn("Unexpected: Could not access view %s state... returning default placement", self.view)
            return self.i, self.j, self.w, self.h, self.i, self.j, self.w, self.h, 1



class MoveResizeOverlay(Overlay, Thread):
    def __init__(self, layout: Layout, view: View):
        Overlay.__init__(self, layout)
        Thread.__init__(self)

        self.layout.update_cursor(False)

        self.view = view

        self.overlay: Optional[_Overlay] = None

        """
        If move has been finished and we are animating towards final position
            (view initial i, view initial j, view final i, view final j, initial time, finished time)
        """
        self._target_view_pos: Optional[tuple[float, float, float, float, float, float]] = None

        """
        If resize has been finished and we are animating towards final size
            (view initial w, view initial h, view final w, view final h, initial time, finished time)
        """
        self._target_view_size: Optional[tuple[float, float, float, float, float, float]] = None

        """
        If we are adjusting viewpoint (after gesture finished or during)
            (layout initial i, layout initial j, layout final i, layout final j, initial time, finished time)
        """
        self._target_layout_pos: Optional[tuple[float, float, float, float, float, float]] = None
        
        self._running = True
        self._wants_close = False

    def post_init(self) -> None:
        logger.debug("MoveResizeOverlay: Starting thread...")
        self.start()

    def run(self) -> None:
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

                    if fi != self.layout.state.i or fj != self.layout.state.j:
                        logger.debug("MoveResizeOverlay: Adjusting viewpoint (%f %f) -> (%f %f)",
                                     self.layout.state.i, self.layout.state.j, fi, fj)
                        self._target_layout_pos = (self.layout.state.i, self.layout.state.j, fi, fj, t, t + conf_anim_t())

                except Exception:
                    logger.warn("Unexpected: Could not access view %s state", self.view)

            if not in_prog and self._wants_close:
                self._running = False

            time.sleep(1. / 120.)

        logger.debug("MoveResizeOverlay: Thread finished")
        self.layout.exit_overlay()

    def on_gesture(self, gesture: Gesture) -> bool:
        if not self._running or self._wants_close:
            logger.debug("MoveResizeOverlay: Rejecting gesture")
            return False

        if isinstance(gesture, TwoFingerSwipePinchGesture):
            logger.debug("MoveResizeOverlay: New TwoFingerSwipePinch")
            self._target_view_pos = None
            self._target_view_size = None

            self.overlay = ResizeOverlay(self.layout, self.view)
            LowpassGesture(gesture).listener(GestureListener(
                self.overlay.on_gesture,
                self.finish
            ))
            return True

        if isinstance(gesture, SingleFingerMoveGesture):
            logger.debug("MoveResizeOverlay: New SingleFingerMove")
            self._target_view_pos = None

            self.overlay = MoveOverlay(self.layout, self.view)
            LowpassGesture(gesture).listener(GestureListener(
                self.overlay.on_gesture,
                self.finish
            ))
            return True

        return False


    def finish(self) -> None:
        logger.debug("MoveResizeOverlay: Finishing gesture")
        if self.overlay is not None:
            ii, ij, iw, ih, fi, fj, fw, fh, t = self.overlay.close()
            self.overlay = None

            if ii != fi or ij != fj:
                self._target_view_pos = (ii, ij, fi, fj, time.time(), time.time() + t)
            if iw != fw or ih != fh:
                self._target_view_size = (iw, ih, fw, fh, time.time(), time.time() + t)


        if not self.layout.modifiers & self.layout.mod:
            logger.debug("MoveResizeOverlay: Requesting close after gesture finish")
            self.close()

    def on_motion(self, time_msec: int, delta_x: float, delta_y: float) -> bool:
        return False

    def on_axis(self, time_msec: int, source: int, orientation: int, delta: float, delta_discrete: int) -> bool:
        return False

    def on_key(self, time_msec: int, keycode: int, state: int, keysyms: str) -> bool:
        if state != PYWM_PRESSED and self.layout.mod_sym in keysyms:
            if self.overlay is None:
                logger.debug("MoveResizeOverlay: Requesting close after Mod release")
                self.close()
            return True

        return False

    def on_modifiers(self, modifiers: int) -> bool:
        return False

    def close(self) -> None:
        if self.overlay is not None:
            self.overlay.close()
        self._wants_close = True

    def pre_destroy(self) -> None:
        self._running = False

    def _exit_transition(self) -> tuple[Optional[LayoutState], float]:
        self.layout.update_cursor(True)
        try:
            # Clean up any possible mishaps - should not be necessary
            view_state = self.layout.state.get_view_state(self.view)
            i = round(view_state.i)
            j = round(view_state.j)
            w = round(view_state.w)
            h = round(view_state.h)

            logger.debug("MoveResizeOverlay: Exiting with animation %d, %d, %d, %d -> %d, %d, %d, %d",
                          view_state.i, view_state.j, view_state.w, view_state.h, i, j, w, h)

            state = self.layout.state.replacing_view_state(
                self.view,
                i=i, j=j, w=w, h=h,
                scale_origin=(None, None), move_origin=(None, None)
            ).focusing_view(self.view)
            state.validate_stack_indices(self.view)
            return state, conf_anim_t()
        except Exception:
            logger.warn("Unexpected: Error accessing view %s state", self.view)
            return None, 0
