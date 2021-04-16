import time
from .panel_endpoint import msg

def cmd(command: str, *args: str) -> None:
    if command == "inhibit-idle":
        try:
            msg({'kind': 'cmd', 'cmd': "inhibit-idle"})
            while True:
                time.sleep(10)
        except:
            pass
        finally:
            msg({'kind': 'cmd', 'cmd': "finish-inhibit-idle"})
    elif command == "launcher":
        msg({'kind': 'launch_app', 'app': " ".join(args)})
    else:
        msg({'kind': 'cmd', 'cmd': command})
