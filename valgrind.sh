#!/bin/bash
PYTHONMALLOC=malloc valgrind python main.py 2> $HOME/.cache/wm_vg_log
