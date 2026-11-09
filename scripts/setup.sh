#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
# Do not recurse into the engine's historical documentation submodules.
git submodule update --init engine plugins/words-net plugins/tex-net
# The inherited source registry expects these roots even before corpus setup.
mkdir -p "$ROOT/engine/source-repo-docs" "$ROOT/engine/source-repo-apiref"
PYTHON=${PYTHON:-python3.12}
"$PYTHON" -m venv "$ROOT/.venv"
"$ROOT/.venv/bin/python" -m pip install -e "$ROOT/engine"
for product in words tex; do
  "$PYTHON" -m venv --without-pip "$ROOT/plugins/$product-net/.venv"
  mkdir -p "$ROOT/workspaces/$product"
done
"$ROOT/.venv/bin/python" "$ROOT/scripts/verify_registration.py"
