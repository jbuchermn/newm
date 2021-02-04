#!/bin/sh
tail -f $(ls -t $HOME/.cache/wm_log* | head -n 1)
