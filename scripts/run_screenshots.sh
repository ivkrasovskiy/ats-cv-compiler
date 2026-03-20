#!/bin/sh
# scripts/run_screenshots.sh
# Takes README screenshots using example data only. Fully self-contained.
# Stops any existing servers on :5173/:8000 and starts its own.

set -e

# ── Kill any existing servers so we own both ports ────────────────────────────
lsof -ti:5173 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 0.5

# ── Ensure Playwright browsers are installed ──────────────────────────────────
if [ ! -d app/e2e/node_modules ]; then
    printf '[…] Installing e2e dependencies...\n'
    npm ci --prefix app/e2e
fi

cd app/e2e && npx playwright install chromium --quiet 2>/dev/null || true && cd ../..

# ── Start frontend dev server ─────────────────────────────────────────────────
printf '[…] Starting frontend dev server...\n'
npm run dev --prefix app/frontend > /tmp/ats-frontend.log 2>&1 &
FRONTEND_PID=$!
trap 'kill $FRONTEND_PID 2>/dev/null; wait $FRONTEND_PID 2>/dev/null' EXIT INT TERM

# Wait up to 30s for frontend to bind
i=0
while [ $i -lt 30 ]; do
    curl -sf http://localhost:5173 > /dev/null 2>&1 && break
    sleep 1; i=$((i+1))
done
if ! curl -sf http://localhost:5173 > /dev/null 2>&1; then
    printf '[✗] Frontend failed to start. Check /tmp/ats-frontend.log\n'
    exit 1
fi
printf '[✓] Frontend ready\n'

# ── Run the screenshot script (it starts its own backend) ─────────────────────
printf '[…] Taking screenshots (uses example data only — no personal data)\n'
node scripts/take_screenshots.mjs

printf '\n[✓] Done. Commit the new files:\n'
printf '      git add docs/screenshots/ && git commit -m "docs: add app screenshots"\n'
