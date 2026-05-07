#!/bin/bash

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
$SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/telegram-brainjammer.py
