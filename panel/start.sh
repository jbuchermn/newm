#!/bin/sh
NW_PATH=/usr/lib/node_modules/nw/bin
TMP_DIR=/tmp/.nw-$$

mkdir -p $TMP_DIR

$NW_PATH/nw $1/build --enable-features=UseOzonePlatform --ozone-platform=wayland --user-data-dir=$TMP_DIR
