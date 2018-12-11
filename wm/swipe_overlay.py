from .lowpass import Lowpass
from .overlay import Overlay, ExitOverlayTransition


class SwipeOverlay(Overlay):
    def __init__(self, layout):
        super().__init__(self)

        self.layout = layout
        self.state = self.layout.state.copy()

        self.x = self.state.i + .5 * self.state.size
        self.y = self.state.j + .5 * self.state.size

        self.initial_x = self.x
        self.initial_y = self.y

        """
        Boundaries of movement
        """
        self.x_bounds = [self.state.min_i + .5 * self.state.size,
                         self.state.max_i + .5 * self.state.size]
        self.y_bounds = [self.state.min_j + .5 * self.state.size,
                         self.state.max_j + .5 * self.state.size]

        """
        Information about which touch we are tracking
        """
        self.tracking_id = None
        self.last_touches = None
        self.delta_x = 0
        self.delta_y = 0

        self.touches_lp_x = None
        self.touches_lp_y = None

        self._set_state()

    def _exit_finished(self):
        self.layout.update_cursor()
        super()._exit_finished()

    def _exit_transition(self):
        self.layout.state = self.state
        return ExitOverlayTransition(
            self, .2,
            i=round(self.x - .5*self.state.size),
            j=round(self.y - .5*self.state.size))

    def _set_state(self):
        self.x = max(self.x, self.x_bounds[0])
        self.x = min(self.x, self.x_bounds[1])
        self.y = max(self.y, self.y_bounds[0])
        self.y = min(self.y, self.y_bounds[1])

        new_state = self.state.copy()
        new_state.i = self.x - .5 * self.state.size
        new_state.j = self.y - .5 * self.state.size

        self.state = new_state

    def _process_touches(self, touches):
        if self.tracking_id is None:
            self.tracking_id = touches[0].id
            self.delta_x = -touches[0].x
            self.delta_y = -touches[0].y

        touch = [t for t in touches if t.id == self.tracking_id]
        if len(touch) == 0:
            """
            Lost touch, find new one

            TODO! Does not seem to work particularly well;
            probably a lost touch is associated with more crappy behaviour
            than just "one touch less in the list"
            """
            new_tracking_id = [t.id for t in touches if t.id in
                               [t.id for t in self.last_touches]][0]
            old_last_touch = [t for t in self.last_touches
                              if t.id == self.tracking_id][0]
            new_last_touch = [t for t in self.last_touches
                              if t.id == new_tracking_id][0]

            self.tracking_id = new_tracking_id
            self.delta_x -= new_last_touch.x - old_last_touch.x
            self.delta_y -= new_last_touch.y - old_last_touch.y
            touch = [t for t in touches if t.id == self.tracking_id]

        self.last_touches = touches
        return touch[0].x + self.delta_x, touch[0].y + self.delta_y

    def on_multitouch_begin(self, touches):
        x, y = self._process_touches(touches.touches)

        self.touches_lp_x = Lowpass(.7)
        self.touches_lp_y = Lowpass(.7)

        self.touches_lp_x.next(x)
        self.touches_lp_y.next(y)

        return True

    def on_multitouch_update(self, touches):
        x, y = self._process_touches(touches.touches)

        x = self.touches_lp_x.next(x)
        y = self.touches_lp_y.next(y)

        self.x = self.initial_x - 4*x

        """
        Only scroll in x direction for now
        """
        # self.y = self.initial_y - 4*y

        self._set_state()
        self.layout.state = self.state
        self.layout.update()

        return True

    def on_multitouch_end(self):
        self.layout.exit_overlay()
        return True

    def on_motion(self, time_msec, delta_x, delta_y):
        return False

    def on_axis(self, time_msec, source, orientation, delta, delta_discrete):
        return False

