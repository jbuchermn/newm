#!/bin/sh
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

cd $HOME
mkdir -p $HOME/.cache

cp .cache/newm_log_bu1 .cache/newm_log_bu2
cp .cache/newm_log .cache/newm_log_bu1
cp .cache/newm_panel_log_bu1 .cache/newm_panel_log_bu2
cp .cache/newm_panel_log .cache/newm_panel_log_bu1

exec python -u $SCRIPTPATH/main.py > $HOME/.cache/newm_log 2>&1
