from __future__ import annotations

from select import select
import evdev # type: ignore
import time
import logging
from threading import Thread
from typing import Callable, Generator

logger = logging.getLogger(__name__)


class Slot:
    def __init__(self, parent: Touchpad, n: int) -> None:
        self.parent = parent
        self.n = n

        self.tracking_id = -1
        self.x = -1
        self.y = -1
        self.z = -1

    def set_tracking_id(self, i: int) -> None:
        self.tracking_id = i
        if self.tracking_id < 0:
            self.x = -1
            self.y = -1
            self.z = -1

    def __str__(self) -> str:
        return "%d: (%d, %d, %d)" % (self.tracking_id, self.x, self.y, self.z)


class TouchpadUpdate:
    def __init__(self, n_touches: int, touches: list[tuple[int, float, float, float]]) -> None:
        """
        touches is an array of tuples (id, x, y, z)
        """
        self.t = time.time()
        self.n_touches = n_touches

        self.touches = touches


class Touchpad(Thread):
    def __init__(self, path: str) -> None:
        super().__init__()
        self.path = path
        self._device = evdev.InputDevice(path)
        self._running = True

        self._n_touches = 0

        self._n_slots = 2
        self._slots: list[Slot] = []

        self._listeners: list[Callable[[TouchpadUpdate], None]] = []

        self.min_x: int = 0
        self.max_x: int = 1
        self.min_y: int = 0
        self.max_y: int = 1
        self.min_z: int = 0
        self.max_z: int = 1
        for code, info in self._device.capabilities()[evdev.ecodes.EV_ABS]:
            if code == evdev.ecodes.ABS_MT_POSITION_X:
                self.min_x = info.min
                self.max_x = info.max
            elif code == evdev.ecodes.ABS_MT_POSITION_Y:
                self.min_y = info.min
                self.max_y = info.max
            elif code == evdev.ecodes.ABS_MT_PRESSURE:
                self.min_z = info.min
                self.max_z = info.max
            elif code == evdev.ecodes.ABS_MT_SLOT:
                self._n_slots = info.max - info.min + 1

    def listener(self, l: Callable[[TouchpadUpdate], None]) -> None:
        self._listeners += [l]

    def _get_slot(self, n: int) -> Slot:
        if n < 0:
            raise Exception("Invalid slot")

        while n >= len(self._slots):
            self._slots += [Slot(self, len(self._slots))]

        return self._slots[n]

    def close(self) -> None:
        self._device.close()

    def synchronize(self) -> None:
        if len([s for s in self._slots if s.tracking_id >= 0]) == 0:
            self._n_touches = 0

        """
        Skip bogus (too early) sync's
        """
        if self._n_touches >= self._n_slots and \
                len([s for s in self._slots if s.tracking_id >= 0]) \
                < self._n_slots:
            return

        update = TouchpadUpdate(
            self._n_touches,
            [(s.tracking_id,
              (s.x - self.min_x)/(self.max_x - self.min_x),
              (s.y - self.min_y)/(self.max_y - self.min_y),
              (s.z - self.min_z)/(self.max_z - self.min_z) if self.min_z is not None else 1.0
              ) for s in self._slots if s.tracking_id >= 0]
        )

        for l in self._listeners:
            l(update)

    def run(self) -> None:
        try:
            slot = 0
            while self._running:
                r, w, x = select([self._device], [], [], 0.1)

                if r:
                    for event in self._device.read():
                        if event.type == evdev.ecodes.EV_SYN:
                            self.synchronize()

                        elif event.type == evdev.ecodes.EV_KEY:
                            if event.value == 1:
                                if event.code == evdev.ecodes.BTN_TOOL_FINGER:
                                    self._n_touches = 1
                                elif event.code == evdev.ecodes.BTN_TOOL_DOUBLETAP:
                                    self._n_touches = 2
                                elif event.code == evdev.ecodes.BTN_TOOL_TRIPLETAP:
                                    self._n_touches = 3
                                elif event.code == evdev.ecodes.BTN_TOOL_QUADTAP:
                                    self._n_touches = 4
                                elif event.code == evdev.ecodes.BTN_TOOL_QUINTTAP:
                                    self._n_touches = 5

                        elif event.type == evdev.ecodes.EV_ABS:
                            if event.code == evdev.ecodes.ABS_MT_SLOT:
                                slot = event.value
                            elif event.code == evdev.ecodes.ABS_MT_TRACKING_ID:
                                self._get_slot(slot).set_tracking_id(event.value)
                            elif event.code == evdev.ecodes.ABS_MT_POSITION_X:
                                self._get_slot(slot).x = event.value
                            elif event.code == evdev.ecodes.ABS_MT_POSITION_Y:
                                self._get_slot(slot).y = event.value
                            elif event.code == evdev.ecodes.ABS_MT_PRESSURE:
                                self._get_slot(slot).z = event.value

        except Exception:
            logger.exception("Touchpad run")
        finally:
            self._device.close()

    def stop(self) -> None:
        self._running = False


def find_all_touchpads() -> Generator[tuple[str, str], None, None]:
    for device in [evdev.InputDevice(d) for d in evdev.list_devices()]:
        if evdev.ecodes.EV_ABS in device.capabilities():
            yield (device.name, device.path)
        device.close()



if __name__ == '__main__':
    import threading
    for n, p in find_all_touchpads():
        print("Found %s at %s" % (n, p))
        touchpad = Touchpad(p)
        touchpad.listener(lambda update: print(update))
        for thread in threading.enumerate():
            print("Pre start:", thread.name)
        touchpad.start()
        try:
            while True:
                time.sleep(1)
                print(".")
        except:
            print("Stopping...")
            touchpad.stop()
            print("Joining...")
            touchpad.join()
            print("...done")

    for thread in threading.enumerate():
        print("Still running:", thread.name)
