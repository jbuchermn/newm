#!/bin/bash
PYTHONMALLOC=malloc valgrind --leak-check=full python main.py 2> $HOME/.cache/newm_log_vg
