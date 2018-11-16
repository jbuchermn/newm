from threading import Thread
from abc import abstractmethod
import time


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
    def __init__(self, animate, dt):
        super().__init__()
        self.animate = animate
        self.dt = dt

    def run(self):
        initial = time.time()
        current = time.time()
        while current - initial < self.dt:
            self.animate._update((current - initial) / self.dt)
            current = time.time()

        self.animate._update_final()


class Animate:
    def __init__(self):
        """
        Animate subclasses need a state member
        """
        self.state = None
        self._interpolate = None
        self._thread = None

    def transition(self, new_state, dt):
        if self._thread is not None:
            return False
        self._interpolate = _StateInterpolate(self.state, new_state)
        self._thread = _Thread(self, dt)
        self._thread.start()

        return True

    def _update(self, perc):
        self.update(self._interpolate.get(perc))

    def _update_final(self):
        self.state = self._interpolate.get(1.)
        self.update(self.state)

        self._interpolate = None
        self._thread = None

    @abstractmethod
    def update(self, state):
        pass
