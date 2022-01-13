from __future__ import annotations
from typing import Any, Callable

import json
import logging
from dasbus.server.template import InterfaceTemplate  # type: ignore
from dasbus.server.publishable import Publishable  # type: ignore
from dasbus.signal import Signal  # type: ignore
from dasbus.connection import SessionMessageBus  # type: ignore
from dasbus.loop import EventLoop  # type: ignore
from dasbus.server.interface import dbus_signal  # type: ignore


logger = logging.getLogger(__name__)

class AuthRequestInterface(InterfaceTemplate):
    __dbus_xml__ = """
    <node>
        <interface name="org.newm.Auth.Request">
            <property access="read" name="Data" type="s"></property>
            <method name="Reply">
                <arg direction="in" name="data" type="s" />
            </method>
        </interface>
    </node>
    """

    @property
    def Data(self) -> str:
        return json.dumps(self.implementation.data)

    def Reply(self, data: str) -> None:
        self.implementation.callback(json.loads(data))


class AuthRequest(Publishable):
    def __init__(self, data: dict[str, Any], callback: Callable[[dict[str, Any]], Any]) -> None:
        self.callback = callback
        self.data = data

    def for_publication(self) -> AuthRequestInterface:
        return AuthRequestInterface(self)


class AuthInterface(InterfaceTemplate):
    __dbus_xml__ = """
    <node>
        <interface name="org.newm.Auth">
            <signal name="Request">
                <arg direction="out" name="req" type="s" />
            </signal>
        </interface>
    </node>
    """

    def connect_signals(self) -> None:
        self.implementation.request.connect(self.Request)

    @dbus_signal
    def Request(self, req: str):  # type: ignore
        pass


class Auth(Publishable):
    def __init__(self) -> None:
        self._request = Signal()

    @property
    def request(self) -> AuthInterface:
        return self._request

    def for_publication(self) -> AuthInterface:
        return AuthInterface(self)


def connect_to_auth(handler: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
    bus = SessionMessageBus()
    proxy = bus.get_proxy("org.newm.Auth", "/org/newm/Auth")

    def handle_request(rid: str) -> None:
        req = bus.get_proxy("org.newm.Auth.Request", rid)
        d = json.loads(req.Data)
        req.Reply(json.dumps(handler(d)))
    proxy.Request.connect(handle_request)

    loop = EventLoop()
    loop.run()

