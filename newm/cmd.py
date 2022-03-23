from __future__ import annotations

import time

from .dbus import send_dbus_command


def cmd(command: str, *args: str) -> None:
    if command == "inhibit-idle":
        try:
            send_dbus_command({"cmd": "inhibit-idle"})
            while True:
                time.sleep(10)
        except:
            pass
        finally:
            send_dbus_command({"cmd": "finish-inhibit-idle"})
    elif command == "launcher":
        send_dbus_command({"cmd": "launcher", "app": " ".join(args)})
    else:
        result = send_dbus_command({"cmd": command, "arg": " ".join(args)})
        if result is not None and "msg" in result:
            print(result["msg"])
