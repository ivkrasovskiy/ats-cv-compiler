.PHONY: dev install test test-onboard test-onboard-claude test-onboard-gemini test-onboard-setup lint fmt check

# ── Local web app (backend + frontend) ────────────────────────────────────────
install:  ## Install Python deps (--extra app) and frontend npm packages
	uv sync --extra app
	cd app/frontend && npm install

dev: install  ## Start backend :8000 + frontend dev server :5173  →  open http://localhost:5173
	@echo "Backend → http://localhost:8000  |  Frontend → http://localhost:5173"
	@echo "Press Ctrl-C to stop both."
	@uv run --extra app cv-app & BACK=$$!; \
	 trap "kill $$BACK 2>/dev/null; wait $$BACK 2>/dev/null" EXIT INT TERM; \
	 cd app/frontend && npm run dev; \
	 wait

# ── Unit tests ─────────────────────────────────────────────────────────────────
test:
	uv run pytest tests/ -q

# ── Lint + format check ────────────────────────────────────────────────────────
lint:
	uv run ruff check src/

fmt:
	uv run ruff format src/

check: lint
	uv run ruff format --check src/

# ── Onboarding integration test ────────────────────────────────────────────────
# Requires: OrbStack installed, `orb` on PATH.
# The cv-test machine is a clean Ubuntu VM with no uv/claude pre-installed.
# macOS home (~) is mounted inside the VM, so your Claude login is inherited.
#
# First-time setup (run once):
#   make test-onboard-setup
#
# Then run the test anytime:
#   make test-onboard

test-onboard-setup:
	@echo "Creating clean Ubuntu VM 'cv-test'..."
	orb create ubuntu cv-test || echo "(already exists, skipping)"
	@echo "Installing Node.js into cv-test..."
	orb run -m cv-test sudo apt-get install -y nodejs npm -q
	@echo "[✓] cv-test VM ready. Run: make test-onboard"

test-onboard: test-onboard-claude test-onboard-gemini  ## run both assistant paths

_test-onboard-run:
	@echo "=== Onboarding integration test: ASSISTANT=$(ASSISTANT) (orb VM: cv-test) ==="
	@echo ""
	@echo "--- Step 1: onboard.sh (full bootstrap, skip exec $(ASSISTANT)) ---"
	orb run -m cv-test bash -c \
	  'cd $(CURDIR) && CV_ONBOARD_TEST=1 CV_ONBOARD_ASSISTANT=$(ASSISTANT) UV_PROJECT_ENVIRONMENT=/tmp/cv-venv-linux bash onboard.sh'
	@echo ""
	@echo "--- Step 2: cv doctor (healthy data) ---"
	orb run -m cv-test bash -c \
	  'export PATH="$$HOME/.npm-global/bin:$$HOME/.local/bin:$$PATH" \
	   && cd $(CURDIR) && UV_PROJECT_ENVIRONMENT=/tmp/cv-venv-linux uv run cv doctor'
	@echo ""
	@echo "--- Step 3: cv doctor (no data/) ---"
	@orb run -m cv-test bash -c \
	  'export PATH="$$HOME/.npm-global/bin:$$HOME/.local/bin:$$PATH" \
	   && cd $(CURDIR) \
	   && mv data data_backup \
	   && UV_PROJECT_ENVIRONMENT=/tmp/cv-venv-linux uv run cv doctor; EXIT=$$?; mv data_backup data; exit $$EXIT' \
	  && { echo "FAIL: expected exit 1, got 0"; exit 1; } || echo "[✓] cv doctor correctly exited 1 with no data/"
	@echo ""
	@echo "--- Step 4: cv build --job false (smoke test) ---"
	orb run -m cv-test bash -c \
	  'export PATH="$$HOME/.npm-global/bin:$$HOME/.local/bin:$$PATH" \
	   && cd $(CURDIR) && UV_PROJECT_ENVIRONMENT=/tmp/cv-venv-linux uv run cv build --job false'
	@echo ""
	@echo "=== All onboarding tests passed (ASSISTANT=$(ASSISTANT)) ==="

test-onboard-claude:  ## force claude path (requires Claude Pro subscription in VM)
	$(MAKE) _test-onboard-run ASSISTANT=claude

test-onboard-gemini:  ## force gemini path (free with Google account)
	$(MAKE) _test-onboard-run ASSISTANT=gemini
