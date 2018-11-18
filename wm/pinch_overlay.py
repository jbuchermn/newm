import math
from .lowpass import Lowpass
from .overlay import Overlay, ExitOverlayTransition
from .animate import Transition


class PinchOverlay(Overlay):
    def __init__(self, layout):
        super().__init__(self)

        self.layout = layout
        self.state = self.layout.state.copy()
        self.state.background_factor *= 1.5

        self.x = self.state.i + .5 * self.state.size
        self.y = self.state.j + .5 * self.state.size
        self.size = self.state.size

        """
        Boundaries of movement
        """
        self.x_bounds = [self.state.min_i + .5 * self.state.size,
                         self.state.max_i + .5 * self.state.size]
        self.y_bounds = [self.state.min_j + .5 * self.state.size,
                         self.state.max_j + .5 * self.state.size]
        self.size_bounds = [1, 5]

        """
        Current multitouch begin state
        """
        self.touches_cog_x = None
        self.touches_cog_y = None
        self.touches_dist = None

        """
        Current multitouch state
        """
        self.touches_lp_cog_x = None
        self.touches_lp_cog_y = None
        self.touches_lp_dist = None

        """
        Current multitouch reference
        """
        self.touches_x = None
        self.touches_y = None
        self.touches_size = None

        self._set_state()

    def keep_alive(self):
        return self.touches_x is not None

    def _exit_finished(self):
        self.layout.rescale()
        self.layout.update_cursor()
        super()._exit_finished()

    def _exit_transition(self):
        self.layout.state = self.state
        return ExitOverlayTransition(
            self, .2,
            background_factor=self.state.background_factor / 1.5,
            size=round(self.size),
            i=round(self.x - .5*self.size),
            j=round(self.y - .5*self.size))

    def _set_state(self):
        self.x = max(self.x, self.x_bounds[0])
        self.x = min(self.x, self.x_bounds[1])
        self.y = max(self.y, self.y_bounds[0])
        self.y = min(self.y, self.y_bounds[1])
        self.size = max(self.size, self.size_bounds[0])
        self.size = min(self.size, self.size_bounds[1])

        new_state = self.state.copy()
        new_state.i = self.x - .5 * self.size
        new_state.j = self.y - .5 * self.size
        new_state.size = self.size

        self.state = new_state

    def _process_touches(self, touches):
        cog_x = (touches[0].x + touches[1].x) / 2.
        cog_y = (touches[0].y + touches[1].y) / 2.

        dist = math.sqrt(
            (touches[0].x - touches[1].x)**2 +
            (touches[0].y - touches[1].y)**2)

        return cog_x, cog_y, max(dist, 0.1)

    def on_multitouch_begin(self, touches):
        self.touches_cog_x, self.touches_cog_y, self.touches_dist = \
            self._process_touches(touches)

        self.touches_x = self.x
        self.touches_y = self.y
        self.touches_size = self.size

        self.touches_lp_cog_x = Lowpass(.9)
        self.touches_lp_cog_y = Lowpass(.9)
        self.touches_lp_dist = Lowpass(.9)

        self.touches_lp_cog_x.next(self.touches_cog_x)
        self.touches_lp_cog_y.next(self.touches_cog_y)
        self.touches_lp_dist.next(self.touches_dist)

        return True

    def on_multitouch_update(self, touches):
        cog_x, cog_y, dist = self._process_touches(touches)

        cog_x = self.touches_lp_cog_x.next(cog_x)
        cog_y = self.touches_lp_cog_y.next(cog_y)
        dist = self.touches_lp_dist.next(dist)

        self.x = self.touches_x - 4*(cog_x - self.touches_cog_x)
        self.y = self.touches_y - 4*(cog_y - self.touches_cog_y)
        self.size = self.touches_size * self.touches_dist / dist

        self._set_state()
        self.layout.update(self.state)

        return True

    def on_multitouch_end(self):
        self.touches_x = None
        self.touches_y = None
        self.touches_size = None
        self.touches_cog_x = None
        self.touches_cog_y = None
        self.touches_size = None

        return True

    def on_motion(self, delta_x, delta_y):
        self.x -= self.size * delta_x
        self.y -= self.size * delta_y
        self._set_state()
        self.layout.update(self.state)

        return True

    def on_axis(self, orientation, delta):
        self.size += 0.01*delta
        self._set_state()
        self.layout.update(self.state)

        return True

