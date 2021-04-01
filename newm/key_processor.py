from __future__ import annotations
from typing import Callable, Any

class TKeyBinding:
    def process(self, pressed: bool, keysyms: str, mod_down: bool, ctrl_down: bool) -> bool:
        pass

    def clear(self) -> None:
        pass


class KeyBinding(TKeyBinding):
    def __init__(self, keys: str, action: Callable[[], Any]) -> None:
        self.mod = False
        self.ctrl = False
        _keys = keys.split("-")
        for k in _keys[:-1]:
            if k == "M":
                self.mod = True
            if k == "C":
                self.ctrl = True

        self.keysym = _keys[-1]
        self.action = action

        self._ready_to_fire = False

    def process(self, pressed: bool, keysyms: str, mod_down: bool, ctrl_down: bool) -> bool:
        if pressed and keysyms == self.keysym and \
                mod_down == self.mod and \
                ctrl_down == self.ctrl:
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

    def process(self, pressed: bool, keysyms: str, mod_down: bool, ctrl_down: bool) -> bool:
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

    def on_key(self, pressed: bool, keysyms: str, mod_down: bool, ctrl_down: bool) -> bool:
        triggered = False
        for b in self.bindings:
            if b.process(pressed, keysyms, mod_down, ctrl_down):
                triggered = True

        return triggered

    def on_other_action(self) -> None:
        for b in self.bindings:
            b.clear()

