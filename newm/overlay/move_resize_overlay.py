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
    from ..layout import Layout, Workspace
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

    def close(self) -> tuple[Workspace, float, float, float, float, float, float, float, float, float]:
        pass


class MoveOverlay(_Overlay):
    def __init__(self, layout: Layout, view: View) -> None:
        self.layout = layout
        self.workspace = layout.workspaces[0]
        self.ws_state = self.layout.state.get_workspace_state(self.workspace)

        self.view = view
        self.i = 0.
        self.j = 0.
        self.w = 1.
        self.h = 1.

        # In case of switched workspace
        self.di = 0
        self.dj = 0

        try:
            view_state, self.ws_state, ws_handle = self.layout.state.find_view(self.view)
            self.workspace = [w for w in self.layout.workspaces if w._handle == ws_handle][0]
            self.i = view_state.i
            self.j = view_state.j
            self.w = view_state.w
            self.h = view_state.h

            self.layout.update(
                self.layout.state.setting_workspace_state(
                    self.workspace, self.ws_state.replacing_view_state(
                        self.view,
                        move_origin=(self.i, self.j)
                    )))
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

        factor = conf_gesture_factor() if not self.layout.state.is_in_overview() else self.ws_state.size

        self.i += factor*(values['delta_x'] - self.last_dx)
        self.j += factor*(values['delta_y'] - self.last_dy)

        i0 = self.i_grid.at(self.i)
        j0 = self.j_grid.at(self.j)

        self.last_dx = values['delta_x']
        self.last_dy = values['delta_y']

        i0 += self.di
        j0 += self.dj

        workspace, i, j, self.w, self.h = self.view.transform_to_closest_ws(self.workspace, i0, j0, self.w, self.h)

        if workspace != self.workspace:
            self.di += (i - i0)
            self.dj += (j - j0)

            self.layout.state.move_view_state(self.view, self.workspace, workspace)
            self.workspace = workspace

        self.layout.state.update_view_state(
            self.view, i=i, j=j, w=self.w, h=self.h)
        self.layout.damage()

    def close(self) -> tuple[Workspace, float, float, float, float, float, float, float, float, float]:
        self._closed = True

        try:

            state, self.ws_state, ws_handle = self.layout.state.find_view(self.view)
            self.workspace = [w for w in self.layout.workspaces if w._handle == ws_handle][0]

            fi, ti = self.i_grid.final()
            fj, tj = self.j_grid.final()

            fi += self.di
            fj += self.dj

            workspace, fi, fj, _, __ = self.view.transform_to_closest_ws(self.workspace, fi, fj, self.w, self.h)

            fi = round(fi)
            fj = round(fj)

            self.w = max(1, round(self.w)) 
            self.h = max(1, round(self.h)) 

            if workspace != self.workspace:
                self.layout.state.move_view_state(self.view, self.workspace, workspace)
                self.workspace = workspace

            logger.debug("Move - Grid finals: %f %f (%f %f)", fi, fj, ti, tj)

            return self.workspace, state.i, state.j, state.w, state.h, fi, fj, round(self.w), round(self.h), max(ti, tj)
        except Exception:
            logger.warn("Unexpected: Could not access view %s state... returning default placement", self.view)
            return self.workspace, self.i, self.j, 1, 1, round(self.i), round(self.j), 1, 1, 1


class ResizeOverlay(_Overlay):
    def __init__(self, layout: Layout, view: View):
        self.layout = layout
        self.workspace = layout.workspaces[0]
        self.ws_state = self.layout.state.get_workspace_state(self.workspace)

        self.view = view
        self.i = 0.
        self.j = 0.
        self.w = 1.
        self.h = 1.

        self.hyst_w = lambda v: v
        self.hyst_h = lambda v: v

        try:
            view_state, self.ws_state, ws_handle = self.layout.state.find_view(self.view)
            self.workspace = [w for w in self.layout.workspaces if w._handle == ws_handle][0]
            self.i = view_state.i
            self.j = view_state.j
            self.w = view_state.w
            self.h = view_state.h

            self.hyst_w = Hysteresis(conf_hyst(), self.w)
            self.hyst_h = Hysteresis(conf_hyst(), self.h)

            self.layout.update(
                self.layout.state.setting_workspace_state(
                    self.workspace, self.ws_state.replacing_view_state(
                        self.view,
                        move_origin=(self.i, self.j),
                        scale_origin=(self.w, self.h)
                    )))

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

        factor = conf_gesture_factor() if not self.layout.state.is_in_overview() else self.ws_state.size
        dw = factor*values['delta_x']
        dh = factor*values['delta_y']

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


    def close(self) -> tuple[Workspace, float, float, float, float, float, float, float, float, float]:
        self._closed = True

        try:
            state = self.layout.state.get_view_state(self.view)
            fi, ti = self.i_grid.final()
            fj, tj = self.j_grid.final()
            fw, tw = self.w_grid.final()
            fh, th = self.h_grid.final()

            logger.debug("Resize - Grid finals: %f %f %f %f (%f %f %f %f)", fi, fj, fw, fh, ti, tj, tw, th)

            return self.workspace, state.i, state.j, state.w, state.h, fi, fj, fw, fh, max(ti, tj, tw, th)
        except Exception:
            logger.warn("Unexpected: Could not access view %s state... returning default placement", self.view)
            return self.workspace, self.i, self.j, self.w, self.h, self.i, self.j, self.w, self.h, 1



class MoveResizeOverlay(Overlay, Thread):
    def __init__(self, layout: Layout, view: View):
        Overlay.__init__(self, layout)
        Thread.__init__(self)

        self.layout.update_cursor(False)

        # TODO: Clean this up a bit (code duplicated -> _Overlay)
        self.view = view
        self.workspace = layout.workspaces[0]
        self.ws_state = self.layout.state.get_workspace_state(self.workspace)

        try:
            view_state, self.ws_state, ws_handle = self.layout.state.find_view(self.view)
            self.workspace = [w for w in self.layout.workspaces if w._handle == ws_handle][0]
        except:
            logger.warn("Unexpected: Could not access view %s state", self.view)

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
                    self.ws_state.i = fi
                    self.ws_state.j = fj
                    self._target_layout_pos = None
                else:
                    perc = (t-it)/(ft-it)
                    self.ws_state.i=ii + perc*(fi-ii)
                    self.ws_state.j=ij + perc*(fj-ij)
                self.layout.damage()

            elif self.overlay is not None:
                try:
                    view_state = self.layout.state.get_view_state(self.view)
                    i, j, w, h = view_state.i, view_state.j, view_state.w, view_state.h
                    i, j, w, h = round(i), round(j), round(w), round(h)

                    fi, fj = self.ws_state.i, self.ws_state.j

                    if i + w > fi + self.ws_state.size:
                        fi = i + w - self.ws_state.size

                    if j + h > fj + self.ws_state.size:
                        fj = j + h - self.ws_state.size

                    if i < fi:
                        fi = i

                    if j < fj:
                        fj = j

                    if fi != self.ws_state.i or fj != self.ws_state.j:
                        logger.debug("MoveResizeOverlay: Adjusting viewpoint (%f %f) -> (%f %f)",
                                     self.ws_state.i, self.ws_state.j, fi, fj)
                        self._target_layout_pos = (self.ws_state.i, self.ws_state.j, fi, fj, t, t + conf_anim_t())

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
            ws, ii, ij, iw, ih, fi, fj, fw, fh, t = self.overlay.close()
            self.overlay = None

            self.workspace = ws
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

            state = self.layout.state.setting_workspace_state(
                self.workspace, self.layout.state.get_workspace_state(self.workspace).replacing_view_state(
                    self.view,
                    i=i, j=j, w=w, h=h,
                    scale_origin=(None, None), move_origin=(None, None)
                ).focusing_view(self.view))
            state.validate_stack_indices(self.view)
            return state, conf_anim_t()
        except Exception:
            logger.warn("Unexpected: Error accessing view %s state", self.view)
            return None, 0
