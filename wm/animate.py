from threading import Thread
import time
from abc import abstractmethod


class Animation:
    def __init__(self, target, prop, func, final):
        self._target = target
        self._prop = prop
        self._func = func
        self._final = final

    def set(self, ts):
        self._target.__dict__[self._prop] = self._func(ts)

    def set_final(self):
        self._target.__dict__[self._prop] = self._final


class InterAnimation:
    def __init__(self, target, prop, delta):
        self._target = target
        self._prop = prop
        self._initial = None
        self._delta = delta

    def set(self, ts):
        if self._initial is None:
            self._initial = self._target.__dict__[self._prop]
        self._target.__dict__[self._prop] = self._initial + \
            ts * self._delta

    def set_final(self):
        self._target.__dict__[self._prop] = self._initial + self._delta


class FinalAnimation:
    def __init__(self, target, prop, delta):
        self._target = target
        self._prop = prop
        self._initial = None
        self._delta = delta

    def set(self, ts):
        if self._initial is None:
            self._initial = self._target.__dict__[self._prop]

    def set_final(self):
        self._target.__dict__[self._prop] = self._initial + self._delta


class AnimateThread(Thread):
    def __init__(self, parent, targets, animations, duration):
        super().__init__()
        self._parent = parent
        self._targets = targets
        self._animations = animations
        self._duration = duration
        self.finished = False

    def run(self):
        initial = time.time()
        ts = initial
        while ts < initial + self._duration:
            for anim in self._animations:
                anim.set((ts - initial)/self._duration)
            for target in self._targets:
                target.update()

            time.sleep(0.02)

            ts = time.time()

        for anim in self._animations:
            anim.set_final()
        for target in self._targets:
            target.update()
        self.finished = True
        self._parent.animation_finished()


class Animate:
    def __init__(self):
        self._current_animation = None
        self._pending_animation = None

    @abstractmethod
    def update(self):
        pass

    def animation_finished(self):
        if self._pending_animation is not None:
            self._current_animation = self._pending_animation
            self._pending_animation = None
            self._current_animation.start()

    def animate(self, animations, duration):
        anim = AnimateThread(self, [self], animations, duration)
        if self._current_animation is not None:
            if not self._current_animation.finished:
                self._pending_animation = anim
                return

        self._current_animation = anim
        self._current_animation.start()

