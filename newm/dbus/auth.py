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
            <property access="read" name="Replied" type="b"></property>
            <method name="Reply">
                <arg direction="in" name="data" type="s" />
            </method>
        </interface>
    </node>
    """

    @property
    def Data(self) -> str:
        return json.dumps(self.implementation.data)

    @property
    def Replied(self) -> bool:
        return self.implementation.replied

    def Reply(self, data: str) -> None:
        if not self.implementation.replied:
            self.implementation.callback(json.loads(data))
        self.implementation.replied = True


class AuthRequest(Publishable):
    def __init__(self, data: dict[str, Any], callback: Callable[[dict[str, Any]], Any]) -> None:
        self.callback = callback
        self.data = data
        self.replied = False

    def for_publication(self) -> AuthRequestInterface:
        return AuthRequestInterface(self)


class AuthInterface(InterfaceTemplate):
    __dbus_xml__ = """
    <node>
        <interface name="org.newm.Auth">
            <signal name="Request">
                <arg direction="out" name="req" type="s" />
            </signal>
            <property access="read" name="Latest" type="s"></property>
        </interface>
    </node>
    """

    def connect_signals(self) -> None:
        self.implementation.request.connect(self.Request)

    @dbus_signal
    def Request(self, req: str):  # type: ignore
        pass

    @property
    def Latest(self) -> str:
        return self.implementation.latest


class Auth(Publishable):
    def __init__(self) -> None:
        self._request = Signal()
        self.latest = ""

    @property
    def request(self) -> AuthInterface:
        return self._request

    def for_publication(self) -> AuthInterface:
        return AuthInterface(self)


def connect_to_auth(handler: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
    bus = SessionMessageBus()
    proxy = bus.get_proxy("org.newm.Auth", "/org/newm/Auth")

    def handle_request(rid: str) -> None:
        req_proxy = bus.get_proxy("org.newm.Auth.Request", rid)
        d = json.loads(req_proxy.Data)
        req_proxy.Reply(json.dumps(handler(d)))
    proxy.Request.connect(handle_request)

    if proxy.Latest != "":
        latest_proxy = bus.get_proxy("org.newm.Auth.Request", proxy.Latest)
        if not latest_proxy.Replied:
            d = json.loads(latest_proxy.Data)
            latest_proxy.Reply(json.dumps(handler(d)))

    loop = EventLoop()
    loop.run()

