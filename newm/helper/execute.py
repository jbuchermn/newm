from __future__ import annotations

import subprocess

def execute(command: str) -> str:
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    return proc.stdout.read().decode() if proc.stdout is not None else ""
