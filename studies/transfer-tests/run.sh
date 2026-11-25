#!/bin/bash
# Driver for the transfer-tests study (Linux/WSL). Usage: run.sh PHASE [--projects a,b]
#   PHASE in: fetch setup baseline variants export verify
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ARTIFACT="$(cd "$HERE/../.." && pwd)"
WORK="${TT_WORK:-$HOME/deps/MarkValidity_TOSEM/transfer-tests}"
PY="$HOME/deps/MarkValidity_TOSEM/python/cpython-3.12.14-linux-x86_64-gnu/bin/python3.12"
phase="$1"; shift
mkdir -p "$WORK/logs"
case "$phase" in
  fetch)
    https_proxy=http://127.0.0.1:7897 http_proxy=http://127.0.0.1:7897 \
      "$PY" -I -B "$HERE/fetch_sources.py" "$ARTIFACT" "$WORK" ;;
  setup|baseline|variants|export)
    "$PY" -I -B "$HERE/run_transfer_tests.py" "$phase" --work "$WORK" --results "$ARTIFACT/results/transfer-tests" "$@" 2>&1 | tee -a "$WORK/logs/$phase.log" ;;
  verify)
    cd "$ARTIFACT" && "${TT_PYTHON:-$PY}" -B -S studies/transfer-tests/verify_transfer_tests.py --results results/transfer-tests ;;
esac
