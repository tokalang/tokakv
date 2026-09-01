#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TOKA_BIN="${TOKA:-toka}"

if ! command -v vhs >/dev/null 2>&1; then
  echo "[FAIL] VHS is required: https://github.com/charmbracelet/vhs" >&2
  exit 1
fi

version_output="$("$TOKA_BIN" --version)"
if [[ "$version_output" != *"1.0.0-rc.10"* ]]; then
  echo "[FAIL] expected Toka 1.0.0-rc.10, got: $version_output" >&2
  exit 1
fi

TOKA_BIN_DIR="$(cd "$(dirname "$TOKA_BIN")" && pwd)"
export PATH="$TOKA_BIN_DIR:$PATH"
export TOKA_LIB="$(cd "$TOKA_BIN_DIR/../lib" && pwd)"
DEMO_WORK="$REPO_ROOT/demo/.quickstart-work"

cleanup() {
  rm -rf "$DEMO_WORK"
}
trap cleanup EXIT

cd "$REPO_ROOT"
cleanup
vhs demo/quickstart.tape

echo "[PASS] rendered demo/tokakv-quickstart.gif"
echo "[PASS] rendered demo/tokakv-quickstart.webm"
