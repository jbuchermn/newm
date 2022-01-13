from __future__ import annotations
from typing import Any, TYPE_CHECKING, Optional

import json
import logging
from dasbus.server.interface import dbus_interface  # type: ignore
from dasbus.connection import SessionMessageBus  # type: ignore


if TYPE_CHECKING:
    from ..layout import Layout

logger = logging.getLogger(__name__)


@dbus_interface("org.newm.Command")
class Command:
    __dbus_xml__ = """
    <node>
        <interface name="org.newm.Command">
            <method name="call">
                <arg direction="in" name="args" type="s" />
                <arg direction="out" name="return" type="s" />
            </method>
        </interface>
    </node>
    """

    def __init__(self, layout: Layout):
        self.layout = layout

    def call(self, args: str) -> str:
        args_dict = json.loads(args)
        if args_dict['cmd'] == 'launcher':
            self.layout.launch_app(args_dict['app'])
            res_dict = { 'msg': 'OK' }
        else:
            res_dict = { 'msg': str(self.layout.command(args_dict['cmd'], args_dict['arg'] if 'arg' in args_dict else None)) }
        return json.dumps(res_dict)


def send_dbus_command(args: dict[str, Any]) -> Optional[dict[str, Any]]:
    bus = SessionMessageBus()
    proxy = bus.get_proxy("org.newm.Command", "/org/newm/Command")
    res = proxy.call(json.dumps(args))
    try:
        return json.loads(res)
    except:
        return None
