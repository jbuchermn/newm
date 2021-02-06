#!/bin/sh
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

cd $HOME

echo "Making PyWM"
$SCRIPTPATH/pywm/make.sh || exit 1;

echo "Starting WM..."
python -u $SCRIPTPATH/main.py ALT > $HOME/.cache/newm_log_$(date --iso-8601=seconds) 2>&1 &

sleep 5
echo "Starting Panel..."
cd $SCRIPTPATH/panel && npm run restart > $HOME/.cache/newm_panel_log_$(date --iso-8601=seconds) 2>&1 &

