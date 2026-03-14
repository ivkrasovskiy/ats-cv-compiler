#!/bin/sh
# onboard.sh — Bootstrap script for ats-cv-compiler
# Run after cloning: bash onboard.sh

set -e

ok()  { printf '[✓] %s\n' "$1"; }
fail() { printf '[✗] %s\n    → %s\n' "$1" "$2"; exit 1; }

# Step 1 — Check Python 3.11+
if command -v python3 > /dev/null 2>&1; then
    PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
    PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
    if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 11 ]; then
        ok "Python ${PY_MAJOR}.${PY_MINOR}"
    else
        fail "Python 3.11+ required (found ${PY_MAJOR}.${PY_MINOR})" \
             "Install from https://www.python.org/downloads/ or via brew install python@3.12"
    fi
else
    fail "Python 3 not found" \
         "Install from https://www.python.org/downloads/ or via brew install python@3.12"
fi

# Step 2 — Install uv (if missing)
if command -v uv > /dev/null 2>&1; then
    ok "uv found ($(uv --version))"
else
    printf '[…] Installing uv...\n'
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Pick up uv in the current shell session
    export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
    if command -v uv > /dev/null 2>&1; then
        ok "uv installed"
    else
        fail "uv installation failed" \
             "Try manually: curl -LsSf https://astral.sh/uv/install.sh | sh"
    fi
fi

# Step 3 — Ensure npm / Node.js is available
if command -v npm > /dev/null 2>&1; then
    ok "npm found ($(node --version))"
else
    if ! command -v brew > /dev/null 2>&1; then
        printf '[…] Installing Homebrew...\n'
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        # Pick up brew in the current shell session (Apple Silicon path)
        export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
        if ! command -v brew > /dev/null 2>&1; then
            fail "Homebrew installation failed" \
                 "Install manually from https://brew.sh then re-run onboard.sh"
        fi
        ok "Homebrew installed"
    fi
    printf '[…] Installing Node.js via Homebrew...\n'
    brew install node
    if command -v npm > /dev/null 2>&1; then
        ok "Node.js installed ($(node --version))"
    else
        fail "Node.js installation failed" \
             "Try manually: brew install node"
    fi
fi

# Step 4 — Install Claude Code (if missing)
if command -v claude > /dev/null 2>&1; then
    ok "Claude Code found"
else
    if command -v npm > /dev/null 2>&1; then
        printf '[…] Installing Claude Code...\n'
        # Try global install; fall back to user-local prefix if permission denied
        if npm install -g @anthropic-ai/claude-code 2>/dev/null; then
            : # success
        else
            printf '[…] Global npm install failed (permissions). Trying user-local prefix...\n'
            NPM_PREFIX="$HOME/.npm-global"
            npm config set prefix "$NPM_PREFIX"
            npm install -g @anthropic-ai/claude-code
        fi
        # Always add npm's configured prefix bin to PATH (handles user-local installs)
        NPM_BIN="$(npm config get prefix)/bin"
        export PATH="$NPM_BIN:$PATH"
        if command -v claude > /dev/null 2>&1; then
            ok "Claude Code installed"
        else
            fail "Claude Code installation failed" \
                 "Try manually: npm install -g @anthropic-ai/claude-code"
        fi
    else
        fail "npm not found (required to install Claude Code)" \
             "Install Node.js from https://nodejs.org/ then re-run onboard.sh"
    fi
fi

# Step 5 — Install Python dependencies
printf '[…] Installing Python dependencies...\n'
uv sync
ok "Python dependencies installed"

# Step 6 — Open Claude Code
printf '\n[✓] Setup complete!\n'
printf 'Opening Claude Code. It will guide you through the rest.\n\n'
if [ "${CV_ONBOARD_TEST:-}" = "1" ]; then
    printf '[TEST MODE] Would exec claude here. Skipping.\n'
    exit 0
fi
exec claude
