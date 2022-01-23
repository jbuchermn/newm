from __future__ import annotations
from typing import Any, TYPE_CHECKING, Optional

import json
import logging
from threading import Thread
from dasbus.loop import EventLoop  # type: ignore
from dasbus.connection import SessionMessageBus, SystemMessageBus  # type: ignore
from dasbus.server.container import DBusContainer  # type: ignore

try:
    from .command import Command
    from .gesture import DBusGestureProvider
    from .auth import AuthRequest, Auth
except: # for __main__
    from command import Command  # type: ignore
    from auth import AuthRequest, Auth  # type: ignore

if TYPE_CHECKING:
    from ..layout import Layout

logger = logging.getLogger(__name__)

class DBusEndpoint(Thread):
    def __init__(self, layout: Layout):
        super().__init__()
        self.layout = layout
        self.gesture_provider: Optional[DBusGestureProvider] = None

        self.bus = SessionMessageBus()
        self.gesture_container = DBusContainer(self.bus, ("org", "newm", "Gestures", "Gesture"))
        self.auth_container = DBusContainer(self.bus, ("org", "newm", "Auth", "Request"))

        self.auth = Auth()

        self.loop = EventLoop()

    def set_gesture_provider(self, provider: DBusGestureProvider) -> None:
        self.gesture_provider = provider

    def stop(self) -> None:
        self.loop.quit()

    def run(self) -> None:
        self.bus.publish_object("/org/newm/Command", Command(self.layout))
        self.bus.register_service("org.newm.Command")


        if self.gesture_provider is not None:
            self.bus.publish_object("/org/newm/Gestures", self.gesture_provider.for_publication())
            self.bus.register_service("org.newm.Gestures")
            self.bus.register_service("org.newm.Gestures.Gesture")

        self.bus.publish_object("/org/newm/Auth", self.auth.for_publication())
        self.bus.register_service("org.newm.Auth")
        self.bus.register_service("org.newm.Auth.Request")

        bus = SystemMessageBus()
        proxy = bus.get_proxy("org.freedesktop.login1", "/org/freedesktop/login1")

        def handle_prepare_for_sleep(sleep: bool) -> None:
            if sleep:
                self.layout.on_sleep()
            else:
                self.layout.on_wakeup()
        proxy.PrepareForSleep.connect(handle_prepare_for_sleep)

        self.loop.run()

    def publish_auth_request(self, req: AuthRequest) -> None:
        key = self.auth_container.to_object_path(req)
        self.auth.request(key)
        self.auth.latest = key


def msg(args: dict[str, Any]) -> Optional[dict[str, Any]]:
    bus = SessionMessageBus()
    proxy = bus.get_proxy("org.newm.Command", "/org/newm/Command")
    res = proxy.call(json.dumps(args))
    try:
        return json.loads(res)
    except:
        return None


if __name__ == '__main__':
    import sys
    import time

    from command import send_dbus_command
    from auth import connect_to_auth

    if sys.argv[1] == "server-cmd":
        DBusEndpoint(None).run()  # type: ignore
    elif sys.argv[1] == "client-cmd":
        print(send_dbus_command({ 'a': 'b' }))
    elif sys.argv[1] == "server-auth":
        e = DBusEndpoint(None)  # type: ignore
        e.start()
        for i in range(5):
            time.sleep(2)
            print("Sending...")
            e.publish_auth_request(AuthRequest({ "a": "c" }, lambda d: print(str(d))))
        e.stop()
    elif sys.argv[1] == "client-auth":
        def handler(d: dict[str, Any]) -> dict[str, Any]:
            print(d)
            return d
        connect_to_auth(handler)
    elif sys.argv[1] == "client-gesture":
        bus = SessionMessageBus()
        proxy = bus.get_proxy("org.newm.Gestures", "/org/newm/Gestures")
        res = proxy.New("swipe-3")
        res_proxy = bus.get_proxy("org.newm.Gestures.Gesture", res)
        time.sleep(.5)
        res_proxy.Update(["delta_x", "delta_y"], [.1, 0.])
        time.sleep(.5)
        res_proxy.Update(["delta_x", "delta_y"], [.2, 0.])
        res_proxy.Terminate()




