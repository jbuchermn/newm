#!/bin/sh
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

cd $HOME

$SCRIPTPATH/../make.sh || exit 1;
echo "\n--------------------------------------\n" >> /tmp/wm_log
echo "Starting WM..."
python -u $SCRIPTPATH/main.py >> /tmp/wm_log 2>&1
