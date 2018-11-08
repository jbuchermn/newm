#!/bin/sh
meson build
ninja -C build
python3 setup.py install --user
