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

# Step 4 — Choose AI assistant
#
# Priority order:
#   1. CV_ONBOARD_ASSISTANT env var set → use it (CI/test override, skips prompt)
#   2. `claude` already on PATH → use claude (skip install, skip question)
#   3. `gemini` already on PATH → use gemini (skip install, skip question)
#   4. Neither found → ask the user
if [ -n "${CV_ONBOARD_ASSISTANT:-}" ]; then
    ASSISTANT="$CV_ONBOARD_ASSISTANT"
    ok "AI assistant: $ASSISTANT (from CV_ONBOARD_ASSISTANT)"
elif command -v claude > /dev/null 2>&1; then
    ASSISTANT=claude
    ok "Claude Code found (using claude)"
elif command -v gemini > /dev/null 2>&1; then
    ASSISTANT=gemini
    ok "Gemini CLI found (using gemini)"
else
    printf '\nWhich AI assistant would you like to use?\n'
    printf '  Gemini CLI is free with any Google account (recommended for most users).\n'
    printf '  Claude Code requires a paid Claude Pro subscription.\n\n'
    printf 'Do you have a paid Claude Pro subscription? [y/N]: '
    read -r CLAUDE_ANSWER
    case "$CLAUDE_ANSWER" in
        [Yy]*) ASSISTANT=claude ;;
        *)     ASSISTANT=gemini ;;
    esac
fi

# Step 5 — Install chosen assistant (if not already on PATH)
_install_npm_package() {
    PKG="$1"
    BIN="$2"
    if command -v "$BIN" > /dev/null 2>&1; then
        return 0
    fi
    if command -v npm > /dev/null 2>&1; then
        printf '[…] Installing %s...\n' "$PKG"
        # Try global install; fall back to user-local prefix if permission denied
        if npm install -g "$PKG" 2>/dev/null; then
            : # success
        else
            printf '[…] Global npm install failed (permissions). Trying user-local prefix...\n'
            NPM_PREFIX="$HOME/.npm-global"
            npm config set prefix "$NPM_PREFIX"
            npm install -g "$PKG"
        fi
        # Always add npm's configured prefix bin to PATH (handles user-local installs)
        NPM_BIN="$(npm config get prefix)/bin"
        export PATH="$NPM_BIN:$PATH"
        if command -v "$BIN" > /dev/null 2>&1; then
            ok "$PKG installed"
        else
            fail "$PKG installation failed" \
                 "Try manually: npm install -g $PKG"
        fi
    else
        fail "npm not found (required to install $PKG)" \
             "Install Node.js from https://nodejs.org/ then re-run onboard.sh"
    fi
}

case "$ASSISTANT" in
    claude) _install_npm_package "@anthropic-ai/claude-code" "claude" ;;
    gemini) _install_npm_package "@google/gemini-cli"        "gemini" ;;
    *)
        fail "Unknown assistant: $ASSISTANT" \
             "Set CV_ONBOARD_ASSISTANT to 'claude' or 'gemini'"
        ;;
esac

# Step 6 — Install Python dependencies
printf '[…] Installing Python dependencies...\n'
uv sync
ok "Python dependencies installed"

# Step 7 — Open chosen assistant
printf '\n[✓] Setup complete!\n'
printf 'Opening %s. It will guide you through the rest.\n' "$ASSISTANT"

printf '\n'
printf '╔══════════════════════════════════════════════════════════════╗\n'
printf '║                        IMPORTANT TIP                        ║\n'
printf '╠══════════════════════════════════════════════════════════════╣\n'
printf '║  At any point, if you have questions about this repo,       ║\n'
printf '║  how to build your CV, or anything else — just open a new   ║\n'
printf '║  terminal and run:                                           ║\n'
printf '║                                                              ║\n'
printf '║      $ %s%-52s║\n' "$ASSISTANT" ""
printf '║                                                              ║\n'
printf '║  Then ask your question in plain English.                    ║\n'
printf '╚══════════════════════════════════════════════════════════════╝\n'
printf '\n'

sleep 5

if [ "${CV_ONBOARD_TEST:-}" = "1" ]; then
    printf '[TEST MODE] Would exec %s. Skipping.\n' "$ASSISTANT"
    exit 0
fi

printf 'Press Enter to continue...'
read -r _ENTER
exec "$ASSISTANT"
