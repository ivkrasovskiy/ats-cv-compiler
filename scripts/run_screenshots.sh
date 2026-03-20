#!/bin/sh
# scripts/run_screenshots.sh
# Takes README screenshots using example data only.
# Requires: uv, node, Playwright (app/e2e/node_modules), frontend dev server on :5173

set -e

# ── Verify frontend is running ────────────────────────────────────────────────
if ! curl -sf http://localhost:5173 > /dev/null 2>&1; then
    printf '[✗] Frontend not running. Start it first:\n'
    printf '      bash start.sh\n'
    printf '    Then re-run this script in another terminal.\n'
    exit 1
fi

# ── Ensure Playwright browsers are installed ──────────────────────────────────
if [ ! -d app/e2e/node_modules ]; then
    printf '[…] Installing e2e dependencies...\n'
    npm ci --prefix app/e2e
fi

# Install Chromium if needed (silent if already present)
cd app/e2e && npx playwright install chromium --quiet 2>/dev/null || true && cd ../..

# ── Run the screenshot script ─────────────────────────────────────────────────
printf '[…] Taking screenshots (uses example data only — no personal data)\n'
node scripts/take_screenshots.mjs

printf '\n[✓] Done. Commit the new files:\n'
printf '      git add docs/screenshots/ && git commit -m "docs: add app screenshots"\n'
