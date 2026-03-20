#!/bin/sh
# scripts/onboard_test.sh — Onboarding integration test (runs inside Docker)
# Simulates a fresh clone: no uv, no deps, with and without data/
#
# Accepts CV_ONBOARD_ASSISTANT env var to choose which assistant to test.
# Defaults to "gemini" (free tier, no auth required in CI).

set -e

PASS=0
FAIL=0
ASSISTANT="${CV_ONBOARD_ASSISTANT:-gemini}"

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

# ── Test 1: onboard.sh (full run, skip exec <assistant>) ──────────────────────
hr "TEST 1: onboard.sh — full bootstrap (ASSISTANT=$ASSISTANT)"
CV_ONBOARD_TEST=1 CV_ONBOARD_ASSISTANT="$ASSISTANT" sh onboard.sh
check "onboard.sh exits 0" "0" "$?"

# onboard.sh installs uv and npm-global binaries into paths that are only exported
# inside its subprocess. Pick them up for the remainder of this test script.
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$HOME/.npm-global/bin:$(npm config get prefix 2>/dev/null)/bin:$PATH"

# ── Test 2: cv doctor — all good (data/ present) ──────────────────────────────
hr "TEST 2: cv doctor — healthy data"
uv run cv doctor
check "cv doctor exits 0 with data" "0" "$?"

# ── Test 3: cv doctor — missing data dir ──────────────────────────────────────
hr "TEST 3: cv doctor — no data/ directory"
mv data data_backup
DOCTOR_EXIT=0; uv run cv doctor || DOCTOR_EXIT=$?
check "cv doctor exits 1 without data" "1" "$DOCTOR_EXIT"
mv data_backup data

# ── Test 4: cv doctor — missing experience ────────────────────────────────────
hr "TEST 4: cv doctor — empty experience/"
mv data/experience data/experience_backup
DOCTOR_EXIT=0; uv run cv doctor || DOCTOR_EXIT=$?
check "cv doctor exits 1 with empty experience" "1" "$DOCTOR_EXIT"
mv data/experience_backup data/experience

# ── Test 5: cv build --job false (smoke test) ─────────────────────────────────
hr "TEST 5: cv build --job false (smoke test)"
uv run cv build --job false
check "cv build exits 0" "0" "$?"

# ── Test 6: verify the chosen assistant binary is on PATH ─────────────────────
hr "TEST 6: $ASSISTANT binary on PATH"
command -v "$ASSISTANT" > /dev/null 2>&1 || true
check "$ASSISTANT found on PATH" "0" "$?"

# ── Test 7: fastapi importable (confirms --extra app worked) ──────────────────
hr "TEST 7: fastapi importable"
uv run python -c "import fastapi" > /dev/null 2>&1
check "fastapi importable" "0" "$?"

# ── Test 8: frontend node_modules present ─────────────────────────────────────
hr "TEST 8: app/frontend/node_modules exists"
[ -d app/frontend/node_modules ] && T8_EXIT=0 || T8_EXIT=1
check "app/frontend/node_modules exists" "0" "$T8_EXIT"

# ── Test 9: cv-app starts and /api/health responds 200 ────────────────────────
hr "TEST 9: cv-app /api/health responds 200"
uv run --extra app cv-app &
APP_PID=$!
i=0
while [ $i -lt 10 ]; do
    curl -sf http://localhost:8000/api/health > /dev/null 2>&1 && break
    sleep 1
    i=$((i + 1))
done
HTTP=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health 2>/dev/null || echo 000)
kill $APP_PID 2>/dev/null; wait $APP_PID 2>/dev/null
check "cv-app /api/health returns 200" "200" "$HTTP"

# ── Test 10: start.sh detects busy port ───────────────────────────────────────
hr "TEST 10: start.sh detects port 8000 busy"
# Bind port 8000 so start.sh should detect and exit 1
nc -l 8000 &
NC_PID=$!
sleep 1
T10_OUT=$(sh start.sh 2>&1 || true)
kill $NC_PID 2>/dev/null; wait $NC_PID 2>/dev/null
echo "$T10_OUT" | grep -q "8000" && T10_EXIT=0 || T10_EXIT=1
check "start.sh detects port 8000 busy" "0" "$T10_EXIT"

# ── Summary ───────────────────────────────────────────────────────────────────
hr "RESULTS"
printf 'Assistant: %s  Passed: %s  Failed: %s\n' "$ASSISTANT" "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
