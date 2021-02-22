#!/bin/sh
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

cd $HOME

cp .cache/newm_log_bu1 .cache/newm_log_bu2
cp .cache/newm_log .cache/newm_log_bu1
cp .cache/newm_panel_log_bu1 .cache/newm_panel_log_bu2
cp .cache/newm_panel_log .cache/newm_panel_log_bu1

echo "Making PyWM"
$SCRIPTPATH/pywm/make.sh || exit 1;

echo "Starting newm..."
python -u $SCRIPTPATH/main.py > $HOME/.cache/newm_log 2>&1 &

sleep 5
echo "Starting panel..."
cd $SCRIPTPATH/panel && npm run start > $HOME/.cache/newm_panel_log 2>&1 &

