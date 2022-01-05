#!/bin/sh
nix-env -f newm.nix -i --arg pywmDir "$1"
