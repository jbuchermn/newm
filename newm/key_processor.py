from __future__ import annotations
from typing import Callable, Any
import logging

from pywm import PyWMModifiers

logger = logging.getLogger(__name__)

class KeyEvent:
    def __init__(self) -> None:
        self.is_mod = False
        self.pressed = False
        self.keysyms = ""
        self.modifiers = PyWMModifiers(0)
        self.last_modifiers = PyWMModifiers(0)

    def set_from_key(self, pressed: bool, keysyms: str, modifiers: PyWMModifiers) -> KeyEvent:
        self.is_mod = False
        self.pressed = pressed
        self.keysyms = keysyms
        self.modifiers = modifiers
        return self

    def set_from_mod(self, modifiers: PyWMModifiers, last_modifiers: PyWMModifiers) -> KeyEvent:
        self.is_mod = True
        self.modifiers = modifiers
        self.last_modifiers = last_modifiers
        return self

class KeyPress:
    def __init__(self, keys: str) -> None:
        self.mod = PyWMModifiers(0)
        _keys = keys.split("-")
        for k in _keys[:-1]:
            if k == "L":
                self.mod.logo = True
            if k == "C":
                self.mod.ctrl = True
            if k == "A":
                self.mod.alt = True
            if k == "1":
                self.mod.mod1 = True
            if k == "2":
                self.mod.mod2 = True
            if k == "3":
                self.mod.mod3 = True
        self.keysym = _keys[-1]
        self.lock_safe = self.keysym.startswith("XF86")

        self._ready_to_fire = False

    def process(self, event: KeyEvent, locked: bool) -> int:
        if locked and not self.lock_safe:
            return -1

        if self.keysym == '':
            if event.is_mod:
                p = event.modifiers.pressed(event.last_modifiers)
                if p == self.mod:
                    self._ready_to_fire = True
                    return 0

                p = event.last_modifiers.pressed(event.modifiers)
                if self._ready_to_fire and \
                        p == self.mod:
                    self._ready_to_fire = False
                    return 1
            else:
                self._ready_to_fire = False

        else:
            if event.is_mod:
                return 0
            else:
                if event.pressed and event.keysyms == self.keysym and \
                        event.modifiers == self.mod:
                    self._ready_to_fire = True
                    return 0

                if not event.pressed and event.keysyms == self.keysym and \
                        self._ready_to_fire:
                    self._ready_to_fire = False
                    return 1

        return -1

    def clear(self) -> None:
        self._ready_to_fire = False

class KeyBinding:
    def __init__(self, keys: str, action: Callable[[], Any]) -> None:
        _keys = keys.strip().split(" ")
        _keys = [k for k in _keys if k != ""]
        self._presses = [KeyPress(k) for k in _keys]
        self._at = 0

        self._action = action

    def process(self, event: KeyEvent, locked: bool) -> int:
        result = self._presses[self._at].process(event, locked)

        if result == 1:
            if self._at == len(self._presses) - 1:
                self._action()
                self._at = 0
                return 1
            else:
                self._at += 1
                return 0
        elif result == 0:
            return 0
        elif result == -1:
            self._at = 0

        return -1

    def clear(self) -> None:
        self._at = 0
        for p in self._presses:
            p.clear()


class KeyProcessor:
    def __init__(self) -> None:
        self.bindings: list[KeyBinding] = []

    def clear(self) -> None:
        self.bindings = []

    def register_bindings(self, *bindings: tuple[str, Callable[[], Any]]) -> None:
        for keys, action in bindings:
            self.bindings += [KeyBinding(keys, action)]

    def on_event(self, event: KeyEvent, locked: bool) -> bool:
        return_True = False
        triggered = False
        for b in self.bindings:
            if triggered:
                b.clear()
            else:
                result = b.process(event, locked)
                if result == 1:
                    triggered = True
                    return_True = True
                if result == 0:
                    return_True = True

        return return_True

    def on_key(self, pressed: bool, keysyms: str, modifiers: PyWMModifiers, locked: bool) -> bool:
        return self.on_event(KeyEvent().set_from_key(pressed, keysyms, modifiers), locked)

    def on_modifiers(self, modifiers: PyWMModifiers, last_modifiers: PyWMModifiers, locked: bool) -> bool:
        return self.on_event(KeyEvent().set_from_mod(modifiers, last_modifiers), locked)

    def on_other_action(self) -> None:
        for b in self.bindings:
            b.clear()

