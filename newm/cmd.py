import time
from .panel_endpoint import msg

def cmd(command: str) -> None:
    if command == "inhibit-idle":
        try:
            msg("inhibit-idle")
            while True:
                time.sleep(10)
        except:
            pass
        finally:
            msg("finish-inhibit-idle")
    else:
        msg(command)
