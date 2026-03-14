#!/bin/sh
# scripts/onboard_test.sh — Onboarding integration test (runs inside Docker)
# Simulates a fresh clone: no uv, no deps, with and without data/

set -e

PASS=0
FAIL=0

check() {
    label="$1"; expected="$2"; actual="$3"
    if [ "$actual" = "$expected" ]; then
        printf '[✓] %s\n' "$label"
        PASS=$((PASS + 1))
    else
        printf '[✗] %s (expected exit %s, got %s)\n' "$label" "$expected" "$actual"
        FAIL=$((FAIL + 1))
    fi
}

hr() { printf '\n─────────────────────────────────────────\n%s\n─────────────────────────────────────────\n' "$1"; }

# ── Test 1: onboard.sh (full run, skip exec claude) ───────────────────────────
hr "TEST 1: onboard.sh — full bootstrap"
export CV_ONBOARD_TEST=1
sh onboard.sh
check "onboard.sh exits 0" "0" "$?"

# ── Test 2: cv doctor — all good (data/ present) ──────────────────────────────
hr "TEST 2: cv doctor — healthy data"
uv run cv doctor
check "cv doctor exits 0 with data" "0" "$?"

# ── Test 3: cv doctor — missing data dir ──────────────────────────────────────
hr "TEST 3: cv doctor — no data/ directory"
mv data data_backup
uv run cv doctor || true
check "cv doctor exits 1 without data" "1" "$?"
mv data_backup data

# ── Test 4: cv doctor — missing experience ────────────────────────────────────
hr "TEST 4: cv doctor — empty experience/"
mv data/experience data/experience_backup
uv run cv doctor || true
check "cv doctor exits 1 with empty experience" "1" "$?"
mv data/experience_backup data/experience

# ── Test 5: cv build --job false (smoke test) ─────────────────────────────────
hr "TEST 5: cv build --job false (smoke test)"
uv run cv build --job false
check "cv build exits 0" "0" "$?"

# ── Summary ───────────────────────────────────────────────────────────────────
hr "RESULTS"
printf 'Passed: %s  Failed: %s\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
