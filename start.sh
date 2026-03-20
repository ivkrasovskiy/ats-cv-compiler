#!/bin/sh
# start.sh — Launch the web app (backend :8000 + frontend :5173)
# Equivalent to `make dev` but works without make and includes pre-flight checks.
# Usage: bash start.sh

set -e

# ── Helpers ───────────────────────────────────────────────────────────────────

ok()   { printf '[✓] %s\n' "$1"; }
info() { printf '[i] %s\n' "$1"; }
fail() {
    printf '[✗] %s\n    → %s\n' "$1" "$2"
    exit 1
}

# _port_busy <port>  →  returns 0 if the port is already in use
_port_busy() {
    lsof -ti:"$1" > /dev/null 2>&1 && return 0
    ss -tlnp 2>/dev/null | grep -q ":$1 " && return 0
    return 1
}

# ── Step 1 — frontend node_modules ───────────────────────────────────────────
if [ ! -d app/frontend/node_modules ]; then
    printf '[…] Frontend node_modules not found. Running npm install...\n'
    npm install --prefix app/frontend
    ok "Frontend dependencies installed"
fi

# ── Step 2 — Port checks ──────────────────────────────────────────────────────
if _port_busy 8000; then
    PID=$(lsof -ti:8000 2>/dev/null || true)
    if [ -n "$PID" ]; then
        fail "Port 8000 is already in use (PID $PID)" \
             "Kill it with:  kill $PID   then re-run bash start.sh"
    else
        fail "Port 8000 is already in use" \
             "Free port 8000 and re-run bash start.sh"
    fi
fi

if _port_busy 5173; then
    PID=$(lsof -ti:5173 2>/dev/null || true)
    if [ -n "$PID" ]; then
        fail "Port 5173 is already in use (PID $PID)" \
             "Kill it with:  kill $PID   then re-run bash start.sh"
    else
        fail "Port 5173 is already in use" \
             "Free port 5173 and re-run bash start.sh"
    fi
fi

# ── Step 3 — Start backend ────────────────────────────────────────────────────
printf '[…] Starting backend on http://localhost:8000 ...\n'
uv run --extra app cv-app &
BACK=$!

trap "kill \$BACK 2>/dev/null; wait \$BACK 2>/dev/null" EXIT INT TERM

ok "Backend started (PID $BACK)"
printf '\n'
printf '  Backend  → http://localhost:8000\n'
printf '  Frontend → http://localhost:5173  ← open this in your browser\n'
printf '\n'
printf '  Press Ctrl-C to stop both.\n'
printf '\n'

# ── Step 4 — Start frontend (blocks until Ctrl-C) ─────────────────────────────
cd app/frontend && npm run dev
