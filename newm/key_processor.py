from __future__ import annotations
from typing import Callable, Any
import logging

from pywm import (
    PYWM_MOD_CTRL,
    PYWM_MOD_ALT,
    PYWM_MOD_MOD2,
    PYWM_MOD_MOD3,
    PYWM_MOD_LOGO,
    PYWM_MOD_MOD5,
)

logger = logging.getLogger(__name__)

class TKeyBinding:
    def process(self, pressed: bool, keysyms: str, mod_down: bool, logo_down: bool, ctrl_down: bool, alt_down: bool, mod1_down: bool, mod2_down: bool, mod3_down: bool, locked: bool) -> bool:
        pass

    def clear(self) -> None:
        pass


class KeyBinding(TKeyBinding):
    def __init__(self, keys: str, action: Callable[[], Any]) -> None:
        self.mod = False
        self.logo = False
        self.ctrl = False
        self.alt = False
        self.mod1 = False
        self.mod2 = False
        self.mod3 = False
        _keys = keys.split("-")
        for k in _keys[:-1]:
            if k == "M":
                self.mod = True
            if k == "L":
                self.logo = True
            if k == "C":
                self.ctrl = True
            if k == "A":
                self.alt = True
            if k == "1":
                self.mod1 = True
            if k == "2":
                self.mod2 = True
            if k == "3":
                self.mod3 = True

        self.keysym = _keys[-1]
        self.action = action
        self.lock_safe = self.keysym.startswith("XF86")

        self._ready_to_fire = False

    def process(self, pressed: bool, keysyms: str, mod_down: bool, logo_down: bool, ctrl_down: bool, alt_down: bool, mod1_down: bool, mod2_down: bool, mod3_down: bool, locked: bool) -> bool:
        if locked and not self.lock_safe:
            return False

        if pressed and keysyms == self.keysym and \
                mod_down == self.mod and \
                logo_down == self.logo and \
                ctrl_down == self.ctrl and \
                alt_down == self.alt and \
                mod1_down == self.mod1 and \
                mod2_down == self.mod2 and \
                mod3_down == self.mod3:
            self._ready_to_fire = True
            return True

        if not pressed and keysyms == self.keysym and \
                self._ready_to_fire:
            self._ready_to_fire = False
            self.action()
            return True

        return False

    def clear(self) -> None:
        pass


class ModPressKeyBinding(TKeyBinding):
    def __init__(self, mod_sym: str, action: Callable[[], Any]) -> None:
        self.mod_sym = mod_sym
        self.action = action
        self._ready_to_fire = False

    def process(self, pressed: bool, keysyms: str, mod_down: bool, logo_down: bool, ctrl_down: bool, alt_down: bool, mod1_down: bool, mod2_down: bool, mod3_down: bool, locked: bool) -> bool:
        if locked:
            return False

        if self.mod_sym not in keysyms:
            self._ready_to_fire = False
            return False

        if pressed:
            self._ready_to_fire = True
        elif self._ready_to_fire:
            self.action()

        return True

    def clear(self) -> None:
        self._ready_to_fire = False


def keybinding_factory(processor: KeyProcessor, keys: str, action: Callable[[], Any]) -> TKeyBinding:
    if keys == "ModPress":
        return ModPressKeyBinding(processor.mod_sym, action)
    else:
        return KeyBinding(keys, action)


class KeyProcessor:
    def __init__(self, mod_sym: str) -> None:
        self.mod_sym = mod_sym
        self.bindings: list[TKeyBinding] = []

    def clear(self) -> None:
        self.bindings = []

    def register_bindings(self, *bindings: tuple[str, Callable[[], Any]]) -> None:
        for keys, action in bindings:
            self.bindings += [keybinding_factory(self, keys, action)]

    def on_key(self, pressed: bool, keysyms: str, modifiers: int, mod: int, locked: bool) -> bool:
        triggered = False
        for b in self.bindings:
            if b.process(pressed, keysyms,
                         bool(modifiers & mod),
                         bool(modifiers & PYWM_MOD_LOGO) and PYWM_MOD_LOGO != mod,
                         bool(modifiers & PYWM_MOD_CTRL) and PYWM_MOD_CTRL != mod,
                         bool(modifiers & PYWM_MOD_ALT) and PYWM_MOD_ALT != mod,
                         bool(modifiers & PYWM_MOD_MOD2) and PYWM_MOD_MOD2 != mod,
                         bool(modifiers & PYWM_MOD_MOD3) and PYWM_MOD_MOD3 != mod,
                         bool(modifiers & PYWM_MOD_MOD5) and PYWM_MOD_MOD5 != mod,
                         locked):
                triggered = True

        return triggered

    def on_other_action(self) -> None:
        for b in self.bindings:
            b.clear()

