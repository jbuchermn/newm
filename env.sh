#!/bin/sh
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

alias nlc="tail -f $HOME/.cache/newm_log"
alias ngp="DISPLAY=\":0\" python3 $SCRIPTPATH/newm/grid.py $HOME/.cache/newm_log"
