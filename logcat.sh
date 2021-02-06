#!/bin/sh
# tail -f $(ls -t $HOME/.cache/newm_log* | head -n 1)
cat $(ls -t $HOME/.cache/newm_log* | head -n 1)
