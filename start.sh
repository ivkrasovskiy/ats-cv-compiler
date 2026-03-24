#!/bin/sh
# start.sh — Launch the web app (backend :8000 + frontend :5173)
# Equivalent to `make dev` but works without make and includes pre-flight checks.
# Usage: bash start.sh [--force]
#   --force   Auto-kill any process already on ports 8000 or 5173 instead of aborting.

set -e

FORCE=0
for arg in "$@"; do
    case "$arg" in
        --force|-f) FORCE=1 ;;
    esac
done

PID_FILE="/tmp/cv-app-$$.pid"

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

# _kill_port <port>  →  kill whatever is on this port
_kill_port() {
    PIDS=$(lsof -ti:"$1" 2>/dev/null || true)
    if [ -n "$PIDS" ]; then
        printf '[i] Killing process(es) on port %s: %s\n' "$1" "$PIDS"
        echo "$PIDS" | xargs kill -9 2>/dev/null || true
        sleep 0.5
    fi
}

# _cleanup — kill the entire process group of the backend, remove PID file
_cleanup() {
    printf '\n[i] Shutting down...\n'
    if [ -f "$PID_FILE" ]; then
        read -r BACK BACK_PGID < "$PID_FILE" 2>/dev/null || true
        rm -f "$PID_FILE"
        if [ -n "$BACK_PGID" ] && [ "$BACK_PGID" -gt 0 ] 2>/dev/null; then
            kill -- -"$BACK_PGID" 2>/dev/null || true
        elif [ -n "$BACK" ]; then
            kill "$BACK" 2>/dev/null || true
        fi
        wait "$BACK" 2>/dev/null || true
    fi
    ok "All processes stopped."
}

trap '_cleanup' EXIT INT TERM

# ── Step 1 — frontend node_modules ───────────────────────────────────────────
if [ ! -d app/frontend/node_modules ]; then
    printf '[…] Frontend node_modules not found. Running npm install...\n'
    npm install --prefix app/frontend
    ok "Frontend dependencies installed"
fi

# ── Step 2 — Port checks ──────────────────────────────────────────────────────
for PORT in 8000 5173; do
    if _port_busy "$PORT"; then
        if [ "$FORCE" = "1" ]; then
            _kill_port "$PORT"
            if _port_busy "$PORT"; then
                fail "Port $PORT is still in use after kill attempt" \
                     "Free port $PORT manually and re-run bash start.sh"
            fi
            ok "Port $PORT cleared"
        else
            PID=$(lsof -ti:"$PORT" 2>/dev/null || true)
            if [ -n "$PID" ]; then
                fail "Port $PORT is already in use (PID $PID)" \
                     "Kill it:  kill $PID   or re-run:  bash start.sh --force"
            else
                fail "Port $PORT is already in use" \
                     "Free port $PORT or re-run:  bash start.sh --force"
            fi
        fi
    fi
done

# ── Step 3 — Start backend ────────────────────────────────────────────────────
printf '[…] Starting backend on http://localhost:8000 ...\n'
uv run --extra app cv-app &
BACK=$!

# Get the process group ID (PGID) of the backend so we can kill all children
sleep 0.2
BACK_PGID=$(ps -o pgid= -p "$BACK" 2>/dev/null | tr -d ' \n' || echo "")
if [ -z "$BACK_PGID" ] || [ "$BACK_PGID" = "0" ]; then
    BACK_PGID=$BACK
fi

# Write PID + PGID to file for _cleanup
printf '%s %s\n' "$BACK" "$BACK_PGID" > "$PID_FILE"

# ── Step 4 — Wait for backend to be ready ────────────────────────────────────
printf '[…] Waiting for backend...\n'
_deadline=$(( $(date +%s) + 20 ))
while [ "$(date +%s)" -lt "$_deadline" ]; do
    if curl -sf http://localhost:8000/api/health > /dev/null 2>&1; then
        break
    fi
    sleep 0.4
done
if ! curl -sf http://localhost:8000/api/health > /dev/null 2>&1; then
    fail "Backend did not start within 20 seconds" "Check logs above for errors"
fi

ok "Backend ready (PID $BACK, PGID $BACK_PGID)"
printf '\n'
printf '  Backend  → http://localhost:8000\n'
printf '  Frontend → http://localhost:5173  ← open this in your browser\n'
printf '\n'
printf '  Press Ctrl-C to stop both.\n'
printf '  Or use the Shutdown button in the app header.\n'
printf '\n'

# ── Step 5 — Start frontend (blocks until Ctrl-C) ─────────────────────────────
npm --prefix app/frontend run dev
