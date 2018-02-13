#!/bin/bash

if [ "$(whoami)" != "root" ]; then
    exec sudo -- "$0" "$@"
fi

node websocket_server.js
