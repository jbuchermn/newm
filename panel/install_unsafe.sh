#!/bin/sh
npm run build-lock
npm run build-notifiers
npm run build-launcher
rm -rf /usr/lib/node_modules/newm-panel
cp -r . /usr/lib/node_modules/newm-panel
