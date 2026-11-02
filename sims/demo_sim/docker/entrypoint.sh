#!/bin/bash -e
################################################################################
##  File:  sim-entrypoint.sh
##  Desc:  Start the Amesa Sim Demo (counter sim) gRPC server
################################################################################

SIM_PATH=${1:-/opt/amesa/sim}
SIM_CONFIG_JSON=${2:-"{}"}
HOST=${HOST:-"0.0.0.0"}
PORT=${PORT:-"1337"}

echo "$0: Starting the Sim Demo (Counter Sim) on ${HOST}:${PORT}"

python3 /opt/amesa/main.py --path "${SIM_PATH}" --config "${SIM_CONFIG_JSON}" --port "${PORT}" --host "${HOST}"