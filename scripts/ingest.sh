#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
case "${1:-}" in
  words|tex) PRODUCT=$1; shift ;;
  *) echo "Usage: $0 words|tex [ingestion options]" >&2; exit 2 ;;
esac
# Protect the product-specific workspace and interpreter from accidental overrides.
for arg in "$@"; do
  case "$arg" in
    --workspace|--workspace=*|--catalog|--catalog=*|--python|--python=*)
      echo "Use the deployment's fixed catalog, workspace and interpreter." >&2; exit 2 ;;
  esac
done
exec "$ROOT/scripts/run-engine.sh" -m adcs.plugins.cli "aspose.$PRODUCT.net" \
  --catalog "$ROOT/config/product-platform-plugins.json" \
  --workspace "$ROOT/workspaces/$PRODUCT" \
  --python "$ROOT/plugins/$PRODUCT-net/.venv/bin/python" "$@"
