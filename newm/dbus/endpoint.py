from __future__ import annotations
from typing import Any, TYPE_CHECKING, Optional

import json
import logging
from threading import Thread
from dasbus.loop import EventLoop  # type: ignore
from dasbus.connection import SessionMessageBus  # type: ignore

from .command import Command

if TYPE_CHECKING:
    from ..layout import Layout

logger = logging.getLogger(__name__)

class DBusEndpoint(Thread):
    def __init__(self, layout: Layout):
        super().__init__()
        self.layout = layout

        self.loop = EventLoop()
        self.bus = SessionMessageBus()
        self.bus.publish_object("/org/newm/Command", Command(self.layout))
        self.bus.register_service("org.newm.Command")

    def stop(self) -> None:
        self.loop.quit()

    def run(self) -> None:
        self.loop.run()


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
    if sys.argv[1] == "server":
        DBusEndpoint(None).run()  # type: ignore
    elif sys.argv[1] == "client":
        print(msg({ 'a': 'b' }))


