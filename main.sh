#!/bin/sh
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

cd $HOME

$SCRIPTPATH/../make.sh || exit 1;
echo "Starting WM..."
python -u $SCRIPTPATH/main.py ALT > $HOME/.cache/wm_log_$(date --iso-8601=seconds) 2>&1
