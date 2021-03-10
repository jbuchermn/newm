from abc import abstractmethod
import time

class Animate:
    def __init__(self):
        self._animation = None

    def _process(self, default_state):
        if self._animation is not None:
            interpolation, s, d, last_ts = self._animation
            ts = time.time()
            if ts - last_ts > 1. / 50.:
                print("WARNING! Slow animation frame (%.2ffps)" % (1. / (ts-last_ts)))
            self._animation = (interpolation, s, d, ts)

            perc = min((ts - s) / d, 1.0)

            if perc >= 0.99:
                self._animation = None

            self.damage()
            return interpolation.get(perc)
        else:
            return default_state

    def _animate(self, interp, dt):
        self._animation = (interp, time.time(), dt, time.time())
        self.damage()

    @abstractmethod
    def damage(self):
        pass
