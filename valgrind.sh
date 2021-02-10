#!/bin/bash
PYTHONMALLOC=malloc valgrind python main.py 2> $HOME/.cache/newm_log_vg
