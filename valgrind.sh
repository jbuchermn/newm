#!/bin/bash
PYTHONMALLOC=malloc valgrind python main.py 2> $HOME/.vg_log
