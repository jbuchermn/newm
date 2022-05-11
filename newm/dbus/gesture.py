from __future__ import annotations
from typing import Callable, TYPE_CHECKING

from dasbus.server.template import InterfaceTemplate  # type: ignore
from dasbus.server.publishable import Publishable  # type: ignore

from ..gestures import Gesture
from ..gestures.provider import GestureProvider

if TYPE_CHECKING:
    from .endpoint import DBusEndpoint

class DBusGestureInterface(InterfaceTemplate):
    __dbus_xml__ = """
    <node>
        <interface name="org.newm.Gestures.Gesture">
            <method name="Update">
                <arg direction="in" name="keys" type="as" />
                <arg direction="in" name="values" type="ad" />
            </method>
            <method name="Terminate" />
        </interface>
    </node>
    """

    def Update(self, keys: list[str], values: list[float]) -> None:
        self.implementation._update({k: v for k, v in zip(keys, values)})

    def Terminate(self) -> None:
        self.implementation._terminate()

class DBusGesture(Publishable, Gesture):
    def __init__(self, kind: str) -> None:
        Gesture.__init__(self, kind)

    def for_publication(self) -> DBusGestureInterface:
        return DBusGestureInterface(self)

class DBusGestureProviderInterface(InterfaceTemplate):
    __dbus_xml__ = """
    <node>
        <interface name="org.newm.Gestures">
            <method name="New">
                <arg direction="in" name="kind" type="s" />
                <arg direction="out" name="id" type="s" />
            </method>
        </interface>
    </node>
    """

    def New(self, kind: str) -> str:
        return self.implementation.on_gesture(kind)

class DBusGestureProvider(GestureProvider, Publishable):
    def __init__(self, endpoint: DBusEndpoint, on_gesture: Callable[[Gesture], bool]) -> None:
        GestureProvider.__init__(self, on_gesture)
        self.endpoint = endpoint

    def on_gesture(self, kind: str) -> str:
        gesture = DBusGesture(kind)
        if self._on_gesture(gesture):
            return self.endpoint.gesture_container.to_object_path(gesture)
        else:
            return ""

    def for_publication(self) -> DBusGestureProviderInterface:
        return DBusGestureProviderInterface(self)
