from threading import Thread
from abc import abstractmethod
import time
import traceback


class _StateInterpolate:
    def __init__(self, state, new_state):
        self.state = state
        self.new_state = new_state
        assert self.state.__class__ == self.new_state.__class__

    def get(self, perc):
        result = self.state.copy()
        for v in self.state.var:
            result.__dict__[v] = \
                self.state.__dict__[v] + perc * \
                (self.new_state.__dict__[v] - self.state.__dict__[v])
        return result


class _Thread(Thread):
    def __init__(self, animate, animation):
        super().__init__()
        self.animate = animate
        self.animation = animation

    def run(self):
        try:
            self.animation.setup()

            initial = time.time()
            current = time.time()
            while current - initial < self.animation.duration:
                self.animation.update((current - initial) /
                                      self.animation.duration)
                current = time.time()

            self.animation.finish()
        except Exception:
            traceback.print_exc()

        self.animate._animation_finished()


class Animation:
    def __init__(self, duration):
        self.duration = duration

    """
    Virtual methods
    """
    def setup(self):
        pass

    def update(self, perc):
        pass

    def finish(self):
        pass


class Transition(Animation):
    def __init__(self, animate, duration, finished_func=None, **new_state):
        super().__init__(duration)
        self._animate = animate
        self._new_state = new_state
        self._interpolate = None
        self._finished_func = finished_func

    def setup(self, new_state=None):
        state = self._animate.state

        if new_state is None:
            new_state = state.copy()
            for k in self._new_state:
                if k.startswith('delta_'):
                    new_state.__dict__[k[5:]] += self._new_state[k]
                else:
                    new_state.__dict__[k] = self._new_state[k]

        self._interpolate = _StateInterpolate(state, new_state)

    def update(self, perc):
        self._animate.update(self._interpolate.get(perc))

    def finish(self):
        self._animate.state = self._interpolate.get(1.)
        self._animate.update(self._animate.state)

        if self._finished_func is not None:
            self._finished_func()


class Animate:
    def __init__(self):
        """
        Animate subclasses need a state member
        """
        self.state = None
        self._thread = None
        self._pending = []

    def animation(self, animation, pend=False):
        if self._thread is not None:
            if not pend:
                return False
            else:
                self._pending += [animation]
                return True

        self._thread = _Thread(self, animation)
        self._thread.start()

        return True

    def _animation_finished(self):
        self._thread = None
        if len(self._pending) > 0:
            p = self._pending[0]
            self._pending = self._pending[1:]
            self.animation(p)

    @abstractmethod
    def update(self, state):
        pass
