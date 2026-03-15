#!/bin/sh
# onboard.sh — Bootstrap script for ats-cv-compiler
# Run after cloning: bash onboard.sh

set -e

# ── Helpers ───────────────────────────────────────────────────────────────────

ok() { printf '[✓] %s\n' "$1"; }

# Set to 1 before any intentional exit so the EXIT trap stays quiet.
_HANDLED_EXIT=0

# Catch unexpected exits caused by `set -e` (a command we didn't anticipate failing).
# Gives the user a helpful next step instead of a silent death.
trap '
  _S=$?
  if [ "$_HANDLED_EXIT" = "0" ] && [ "$_S" -ne 0 ]; then
    printf "\n[!] onboard.sh stopped unexpectedly (exit status %d).\n" "$_S"
    printf "    Look at the error printed above for the cause.\n"
    if [ -n "${ASSISTANT:-}" ]; then
      printf "\n    Your AI assistant is already installed. Open a new terminal and run:\n"
      printf "      $ %s\n" "$ASSISTANT"
      printf "    Describe what went wrong and ask it to help you fix onboard.sh.\n"
    else
      printf "\n    Fix the error above and re-run:  bash onboard.sh\n"
      printf "    Or install an AI assistant for help (then re-run onboard.sh):\n"
      printf "      Free (Google account):  npm install -g @google/gemini-cli\n"
      printf "      Paid (Claude Pro):      npm install -g @anthropic-ai/claude-code\n"
    fi
  fi
' EXIT

# fail <what went wrong> <how to fix it>
# Hard-stops the script with a clear message. Once $ASSISTANT is set, also
# tells the user which AI to open for help.
fail() {
    _HANDLED_EXIT=1
    printf '[✗] %s\n    → %s\n' "$1" "$2"
    if [ -n "${ASSISTANT:-}" ]; then
        printf '    → Still stuck? Open a new terminal and run: $ %s\n' "$ASSISTANT"
    fi
    exit 1
}

# _pause — wait for Enter before continuing (skipped in test mode)
_pause() {
    if [ "${CV_ONBOARD_TEST:-}" = "1" ]; then return; fi
    printf 'Press Enter to continue...'
    read -r _ENTER
    printf '\n'
}

# ── Step 1 — Ensure npm / Node.js ────────────────────────────────────────────
# The AI assistant is installed via npm, so this must come first.
if command -v npm > /dev/null 2>&1; then
    ok "npm found ($(node --version))"
else
    if ! command -v brew > /dev/null 2>&1; then
        printf '[…] Installing Homebrew (you may be prompted for your password)...\n'
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
        if ! command -v brew > /dev/null 2>&1; then
            _HANDLED_EXIT=1
            printf '[✗] Homebrew installation failed.\n'
            printf '    → Install manually: https://brew.sh\n'
            printf '    → Or install Node.js directly: https://nodejs.org/\n'
            printf '    → Then re-run: bash onboard.sh\n'
            exit 1
        fi
        ok "Homebrew installed"
    fi
    printf '[…] Installing Node.js via Homebrew...\n'
    brew install node
    if command -v npm > /dev/null 2>&1; then
        ok "Node.js installed ($(node --version))"
    else
        _HANDLED_EXIT=1
        printf '[✗] Node.js installation failed.\n'
        printf '    → Try:  brew install node\n'
        printf '    → Or download from: https://nodejs.org/\n'
        printf '    → Then re-run: bash onboard.sh\n'
        exit 1
    fi
fi

# ── Step 2 — Choose AI assistant ─────────────────────────────────────────────
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

# ── Step 3 — Install chosen assistant ────────────────────────────────────────
_install_npm_package() {
    PKG="$1"
    BIN="$2"
    if command -v "$BIN" > /dev/null 2>&1; then
        ok "$BIN already installed"
        return 0
    fi
    printf '[…] Installing %s...\n' "$PKG"

    # Attempt global install; on permission failure fall back to user-local prefix.
    if npm install -g "$PKG" 2>/tmp/npm_err_$$; then
        NPM_BIN="$(npm config get prefix)/bin"
    else
        # Check whether the failure was a permission error or something else.
        if grep -qiE 'EACCES|permission denied' /tmp/npm_err_$$ 2>/dev/null; then
            printf '[…] Permission denied for global install. Using user-local prefix (~/.npm-global)...\n'
        else
            # Non-permission failure — show the actual error and stop.
            cat /tmp/npm_err_$$
            rm -f /tmp/npm_err_$$
            fail "$PKG installation failed" \
                 "Try manually: npm install -g $PKG"
        fi
        rm -f /tmp/npm_err_$$

        NPM_PREFIX="$HOME/.npm-global"
        mkdir -p "$NPM_PREFIX/bin"
        npm install -g "$PKG" --prefix "$NPM_PREFIX"
        NPM_BIN="$NPM_PREFIX/bin"

        # Persist the PATH addition to the user's shell profile so future
        # terminals can find the binary without re-running onboard.sh.
        LINE="export PATH=\"$NPM_BIN:\$PATH\""
        SHELL_RC=""
        case "${SHELL:-$(command -v zsh || true)}" in
            */zsh)  SHELL_RC="$HOME/.zshrc" ;;
            */bash) SHELL_RC="$HOME/.bash_profile" ;;
        esac
        if [ -n "$SHELL_RC" ] && ! grep -qF "$NPM_BIN" "$SHELL_RC" 2>/dev/null; then
            printf '\n# Added by ats-cv-compiler onboard.sh\n%s\n' "$LINE" >> "$SHELL_RC"
            printf '[i] Added %s to %s (takes effect in new terminals).\n' "$NPM_BIN" "$SHELL_RC"
        fi
    fi
    rm -f /tmp/npm_err_$$

    export PATH="$NPM_BIN:$PATH"

    if command -v "$BIN" > /dev/null 2>&1; then
        ok "$PKG installed"
    else
        fail "$BIN installed but not found on PATH" \
             "Open a new terminal and try: npm install -g $PKG"
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

# ─────────────────────────────────────────────────────────────────────────────
# From this point on $ASSISTANT is installed.
# Every fail() call will print "Still stuck? Open a new terminal and run: $ $ASSISTANT"
# ─────────────────────────────────────────────────────────────────────────────

# ── Step 4 — Check Python 3.11+ ──────────────────────────────────────────────
if command -v python3 > /dev/null 2>&1; then
    PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
    PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
    if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 11 ]; then
        ok "Python ${PY_MAJOR}.${PY_MINOR}"
    else
        fail "Python 3.11+ required (found ${PY_MAJOR}.${PY_MINOR})" \
             "brew install python@3.12   or   https://www.python.org/downloads/"
    fi
else
    fail "Python 3 not found" \
         "brew install python@3.12   or   https://www.python.org/downloads/"
fi

# ── Step 5 — Install uv ──────────────────────────────────────────────────────
if command -v uv > /dev/null 2>&1; then
    ok "uv found ($(uv --version))"
else
    printf '[…] Installing uv...\n'
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
    if command -v uv > /dev/null 2>&1; then
        ok "uv installed"
    else
        fail "uv installation failed" \
             "Try manually: curl -LsSf https://astral.sh/uv/install.sh | sh"
    fi
fi

# ── Step 6 — Install Python dependencies (soft failure) ──────────────────────
# Non-fatal: the AI assistant is already installed and can help debug any issue.
printf '[…] Installing Python dependencies...\n'
UV_SYNC_OK=1
if ! uv sync; then
    UV_SYNC_OK=0
    printf '\n[!] Python dependency installation failed (see error above).\n'
    printf '    The  uv run cv  commands will not work until this is fixed.\n'
    printf '    Re-run  bash onboard.sh  once you have resolved it, or ask:\n'
    printf '      $ %s\n\n' "$ASSISTANT"
else
    ok "Python dependencies installed"
fi

# ── Step 7 — Quick orientation tour (non-skippable, Enter-gated) ─────────────
if [ "$UV_SYNC_OK" = "1" ]; then
    printf '\n[✓] Setup complete! Before we open %s, here is a 1-minute overview.\n\n' "$ASSISTANT"
else
    printf '\n[!] Setup partially complete (uv sync failed — see above).\n'
    printf '    Opening %s so you can ask it to help fix the remaining issue.\n\n' "$ASSISTANT"
fi

# ── Screen 1: core workflow ───────────────────────────────────────────────────
printf '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
printf ' 1 of 5  —  HOW IT WORKS\n'
printf '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
printf '\n'
printf '  Your career data lives in the  data/  folder:\n'
printf '\n'
printf '    data/profile.md      ← your name, headline, contact info\n'
printf '    data/skills.md       ← skill categories\n'
printf '    data/education.md    ← degrees\n'
printf '    data/projects/       ← one file per project you have worked on\n'
printf '    data/experience/     ← work history (auto-generated from projects)\n'
printf '\n'
printf '  Note: experience entries are created automatically by the AI from\n'
printf '  your project descriptions — you do not need to write them by hand.\n'
printf '\n'
printf '  To build your CV:\n'
printf '\n'
printf '    uv run cv build --job false\n'
printf '\n'
printf '  Output lands in  out/cv_generic.pdf  — open it to see the result.\n'
printf '\n'
_pause

# ── Screen 2: job targeting ───────────────────────────────────────────────────
printf '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
printf ' 2 of 5  —  APPLYING TO A SPECIFIC JOB\n'
printf '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
printf '\n'
printf '  For each job you want to apply to:\n'
printf '\n'
printf '    1. Copy the job description text (from any job board)\n'
printf '    2. Paste it into a new file under the  jobs/  folder,\n'
printf '       e.g.  jobs/google.md  or  jobs/stripe.md\n'
printf '       (one file per job — any filename ending in .md)\n'
printf '\n'
printf '  Then build your tailored CV:\n'
printf '\n'
printf '    uv run cv build --job jobs/google.md\n'
printf '\n'
printf '  The tool reads the job description and automatically highlights\n'
printf '  the experience and skills most relevant to that role.\n'
printf '\n'
printf '  To also have the AI rewrite your bullet points for that job:\n'
printf '\n'
printf '    uv run cv build --llm agents --job jobs/google.md\n'
printf '\n'
printf '  The AI only uses facts already in your data files — it never\n'
printf '  makes anything up.\n'
printf '\n'
_pause

# ── Screen 3: manual edits via markdown ──────────────────────────────────────
printf '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
printf ' 3 of 5  —  MAKING MANUAL TWEAKS\n'
printf '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
printf '\n'
printf '  Every build produces a Markdown file alongside the PDF:\n'
printf '\n'
printf '    out/cv_generic.md   ← the full CV as plain text\n'
printf '\n'
printf '  You can open this file in any text editor, fix a single word,\n'
printf '  remove a bullet, or reorder sections — whatever you need.\n'
printf '\n'
printf '  Once you are happy with your edits, turn it back into a PDF:\n'
printf '\n'
printf '    uv run cv build --from-markdown out/cv_generic.md\n'
printf '\n'
printf '  This is the fastest way to make a quick one-off fix without\n'
printf '  touching your source data files.\n'
printf '\n'
_pause

# ── Screen 4: customisation ───────────────────────────────────────────────────
printf '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
printf ' 4 of 5  —  EVERYTHING IS CUSTOMISABLE\n'
printf '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
printf '\n'
printf '  Nothing is hardcoded. Every part of the output is driven by\n'
printf '  plain files you can read and change:\n'
printf '\n'
printf '    templates/           ← PDF layout (fonts, spacing, sections)\n'
printf '    prompts/             ← AI instructions for bullet rewriting\n'
printf '    config/llm.env       ← which AI model to use, timeouts, etc.\n'
printf '\n'
printf '  Want a two-column layout? A different font? A new section?\n'
printf '  It is all just files — no code changes required for most tweaks.\n'
printf '\n'
_pause

# ── Screen 5: how to change things ───────────────────────────────────────────
printf '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
printf ' 5 of 5  —  HOW TO MAKE CHANGES\n'
printf '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
printf '\n'
printf '  Your AI assistant knows this entire codebase. If you want to\n'
printf '  change anything — layout, prompts, logic — just ask it:\n'
printf '\n'
printf '      $ %s\n' "$ASSISTANT"
printf '\n'
printf '  Describe what you want in plain English. Examples:\n'
printf '    "Add a Languages section between Skills and Education"\n'
printf '    "Make the bullet points shorter — max 15 words each"\n'
printf '    "Use a more compact layout so everything fits on one page"\n'
printf '\n'
printf '  After the assistant makes changes, always run the tests to make\n'
printf '  sure nothing broke:\n'
printf '\n'
printf '      uv run pytest tests/ -q\n'
printf '\n'
_pause

# ── Final reminder ────────────────────────────────────────────────────────────
printf '╔══════════════════════════════════════════════════════════════╗\n'
printf '║                        REMEMBER                              ║\n'
printf '╠══════════════════════════════════════════════════════════════╣\n'
printf '║  For any question about this repo, open a new terminal       ║\n'
printf '║  and run:                                                    ║\n'
printf '║                                                              ║\n'
printf '║      $ %-54s║\n' "$ASSISTANT"
printf '║                                                              ║\n'
printf '║  Then ask in plain English. It knows everything.             ║\n'
printf '╚══════════════════════════════════════════════════════════════╝\n'
printf '\n'

_HANDLED_EXIT=1
if [ "${CV_ONBOARD_TEST:-}" = "1" ]; then
    printf '[TEST MODE] Would exec %s. Skipping.\n' "$ASSISTANT"
    exit 0
fi

printf 'Press Enter to open %s...' "$ASSISTANT"
read -r _ENTER
exec "$ASSISTANT"
