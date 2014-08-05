#!/bin/bash
# Helper script to run python process in virtualenv with supervisord.
VENV=$1
if [ -z $VENV ]; then
    echo "usage: runinenv [virtualenv_path] CMDS"
    exit 1
fi
. ${VENV}/bin/activate
shift 1
echo "Executing $@ in VENV:${VENV}"
exec "$@"
deactivate
