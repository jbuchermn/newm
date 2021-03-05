#!/bin/bash
PYTHONMALLOC=malloc valgrind --leak-check=full python -c "from newm import run; run()" 2> $HOME/.cache/newm_log_vg
