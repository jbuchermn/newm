#!/usr/bin/env python3
import sys
from .panel import panel


def main():
    """Entry point for newm-panel-basic command."""
    if len(sys.argv) > 1:
        panel(sys.argv[1])
    else:
        print("Usage: newm-panel-basic <config_file>")
        sys.exit(1)


if __name__ == "__main__":
    main()