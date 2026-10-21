#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
NODE="$SCRIPT_DIR/../../.runtime/node/bin/node"
if [ ! -x "$NODE" ]; then NODE=$(command -v node); fi
exec "$NODE" "$SCRIPT_DIR/validate-spawns.mjs" "$@"
