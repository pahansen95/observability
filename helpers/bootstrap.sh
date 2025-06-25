#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
root="$(cd "$script_dir/.." && pwd)"

export PYTHONPATH="$root${PYTHONPATH+:$PYTHONPATH}"
exec python3 -m helpers.bootstrap "$@"
