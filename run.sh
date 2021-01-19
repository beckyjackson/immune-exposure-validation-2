#!/usr/bin/env nix-shell
#!nix-shell -i bash -p bash python38Full
trap 'exit 0' 1 2 15
source settings.env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=src/server/server.py
flask run --port ${PORT}
