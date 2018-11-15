#!/bin/sh
echo "\n--------------------------------------\n" >> /tmp/wm_log
python -u main.py >> /tmp/wm_log 2>&1
