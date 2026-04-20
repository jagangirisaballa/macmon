# macmon — Full Backlog Specs

---

## CR-001: Pre-publish fixes

**Priority:** High — must complete before LinkedIn post / PyPI publish
**Status:** Open

### Change 1 — Fix install story
**File:** `pyproject.toml:3`
**Problem:** Wrong build backend causes `pip install macmon` to fail.
**Fix:** Change `setuptools.backends.legacy:build` → `setuptools.build_meta`

### Change 2 — Bind to localhost by default
**File:** `macmon/cli.py:36`
**Problem:** Server binds to `0.0.0.0` — anyone on same WiFi can access dashboard and kill processes.
**Fix:** Default host to `127.0.0.1`. Add explicit `--host` flag for opt-in network access.

### Change 3 — Remove Google Fonts
**File:** `macmon/static/index.html:7-9`
**Problem:** README says "nothing sent anywhere" but page loads fonts from fonts.googleapis.com.
**Fix:** Remove three Google Fonts `<link>` tags. Update `--f-sans` and `--f-mono` to system font stack.

---

## Issues deferred to v1.1 (post-publish)

See ISSUES.md for full specs on C-01 through L-03. All deferred until after first public release.

---
