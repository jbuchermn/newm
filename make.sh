#!/bin/sh
meson build
ninja -C build
python setup.py install --user
