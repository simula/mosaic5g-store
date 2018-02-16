#!/bin/bash

if [ "$(whoami)" != "root" ]; then
    exec sudo -- "$0" "$@"
fi

apt install npm nodejs-legacy
npm install websocket
npm install path
npm install url
npm install http

