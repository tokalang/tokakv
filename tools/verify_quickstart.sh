#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TOKA_BIN="${TOKA:-toka}"
TOKAKV_SOURCE="${TOKAKV_SOURCE:-}"
VERIFY_ROOT="$(mktemp -d /tmp/tokakv-quickstart.XXXXXX)"

cleanup() {
  rm -rf "$VERIFY_ROOT"
}
trap cleanup EXIT

fail_with_log() {
  local label="$1"
  local stdout_file="$2"
  local stderr_file="$3"
  echo "[FAIL] $label" >&2
  sed -n '1,240p' "$stdout_file" >&2 || true
  sed -n '1,240p' "$stderr_file" >&2 || true
  exit 1
}

version_output="$("$TOKA_BIN" --version)"
if [[ "$version_output" != *"1.0.0-rc.10"* ]]; then
  echo "[FAIL] expected Toka 1.0.0-rc.10, got: $version_output" >&2
  exit 1
fi

"$TOKA_BIN" new "$VERIFY_ROOT/tokakv-tour" >"$VERIFY_ROOT/new.stdout" 2>"$VERIFY_ROOT/new.stderr"
cd "$VERIFY_ROOT/tokakv-tour"

if [[ -n "$TOKAKV_SOURCE" ]]; then
  "$TOKA_BIN" add "$TOKAKV_SOURCE" >"$VERIFY_ROOT/add.stdout" 2>"$VERIFY_ROOT/add.stderr"
else
  "$TOKA_BIN" add tokakv >"$VERIFY_ROOT/add.stdout" 2>"$VERIFY_ROOT/add.stderr"
fi

cp "$REPO_ROOT/examples/ten-minute-tour/src/main.tk" src/main.tk

if ! "$TOKA_BIN" run >"$VERIFY_ROOT/first.stdout" 2>"$VERIFY_ROOT/first.stderr"; then
  fail_with_log "first quickstart run" "$VERIFY_ROOT/first.stdout" "$VERIFY_ROOT/first.stderr"
fi
if ! "$TOKA_BIN" run >"$VERIFY_ROOT/second.stdout" 2>"$VERIFY_ROOT/second.stderr"; then
  fail_with_log "second quickstart run" "$VERIFY_ROOT/second.stdout" "$VERIFY_ROOT/second.stderr"
fi

grep -Fq "[TokaKV] FIRST RUN" "$VERIFY_ROOT/first.stdout" ||
  fail_with_log "missing first-run marker" "$VERIFY_ROOT/first.stdout" "$VERIFY_ROOT/first.stderr"
grep -Fq "snapshot: account:42 = 100" "$VERIFY_ROOT/first.stdout" ||
  fail_with_log "snapshot did not retain value 100" "$VERIFY_ROOT/first.stdout" "$VERIFY_ROOT/first.stderr"
grep -Fq "latest:   account:42 = 125" "$VERIFY_ROOT/first.stdout" ||
  fail_with_log "latest read did not return value 125" "$VERIFY_ROOT/first.stdout" "$VERIFY_ROOT/first.stderr"
grep -Fq "lease after close: 125" "$VERIFY_ROOT/first.stdout" ||
  fail_with_log "lease did not remain valid after close" "$VERIFY_ROOT/first.stdout" "$VERIFY_ROOT/first.stderr"

grep -Fq "[TokaKV] SECOND RUN" "$VERIFY_ROOT/second.stdout" ||
  fail_with_log "missing second-run marker" "$VERIFY_ROOT/second.stdout" "$VERIFY_ROOT/second.stderr"
grep -Fq "recovered: account:42 = 125" "$VERIFY_ROOT/second.stdout" ||
  fail_with_log "WAL recovery did not restore value 125" "$VERIFY_ROOT/second.stdout" "$VERIFY_ROOT/second.stderr"
grep -Fq "sequence: 2" "$VERIFY_ROOT/second.stdout" ||
  fail_with_log "WAL recovery did not restore sequence 2" "$VERIFY_ROOT/second.stdout" "$VERIFY_ROOT/second.stderr"
grep -Fq "RECOVERY VERIFIED" "$VERIFY_ROOT/second.stdout" ||
  fail_with_log "missing recovery success marker" "$VERIFY_ROOT/second.stdout" "$VERIFY_ROOT/second.stderr"

echo "[PASS] RC10 TokaKV quickstart"
sed -n '1,80p' "$VERIFY_ROOT/first.stdout"
sed -n '1,80p' "$VERIFY_ROOT/second.stdout"
