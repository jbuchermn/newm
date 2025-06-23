#!/usr/bin/env python3
import sys
import argparse
from .run import run


def start_newm():
    """Entry point for start-newm command."""
    print("newm - args are %s" % str(sys.argv), flush=True)
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-p", "--profile", action="store_true")
    parser.add_argument("-c", "--config-file", type=str, default=None)
    
    args = parser.parse_args()
    
    print(args)
    
    run(args.debug, args.profile, args.config_file)


if __name__ == "__main__":
    start_newm()