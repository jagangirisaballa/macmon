# macmon — Full Backlog Specs

---

## CR-007 — GitHub Actions automated release workflow — COMPLETED 2026-04-22

**Goal:** Automate PyPI publish + GitHub Release on every version tag push.
**File:** `.github/workflows/release.yml`
**Trigger:** Push of any `v*` tag
**Steps:** checkout → build → twine upload (skips if version already on PyPI) → softprops/action-gh-release
**Secret required:** `PYPI_TOKEN` in GitHub repo secrets (project-scoped PyPI API token)
**Usage:** `git tag vX.Y.Z && git push origin vX.Y.Z` — everything else is automatic.

---

## CR-008 — Stop button in dashboard header — COMPLETED 2026-04-22

**Goal:** Allow users to stop macmon from the browser without going back to Terminal.
**Files:** `macmon/server.py`, `macmon/static/index.html`
**Backend:** Added `POST /api/shutdown` — sends SIGTERM to own PID after 0.3s delay.
**Frontend:** Square stop icon button (⏹) added left of restart button. On click: confirmation dialog,
POST /api/shutdown, shows "macmon stopped. Run macmon start to reopen." overlay.

---

## CR-009 — macmon stop kills all processes — COMPLETED 2026-04-22

**Goal:** Fix critical bug where `macmon stop` left orphan processes running (sending notifications,
consuming RAM) because it only killed the PID in `~/.macmon.pid`.
**File:** `macmon/cli.py`
**Root cause:** Dashboard restart spawns a new uvicorn process and updates the PID file, but the old
process could remain. Any mismatch between PID file and actual process left macmon running silently.
**Fix:** Added `_find_macmon_pids()` that scans all processes for `uvicorn macmon.server` in cmdline.
`cmd_stop()` now kills ALL matching processes regardless of PID file state. `cmd_status` uses same scan.
**Nuclear fallback always works:** `pkill -f "uvicorn macmon.server"`

---

## CR-010 — Update check on macmon start — COMPLETED 2026-04-22

**Goal:** Users on old versions get notified of updates automatically — especially important after the
CR-009 bug fix where users on v1.1.1 or earlier have the orphan-process bug.
**File:** `macmon/cli.py`
**Implementation:** `_check_for_update()` — hits `https://pypi.org/pypi/macmon/json`, compares latest
version to `macmon.__version__`, prints one-line notice with exact upgrade command. 3s timeout.
Silent on any failure (no internet, timeout, etc). Called after successful start and when already running.
**Output when outdated:**
  ⚠ Update available: v1.1.3 (you have v1.0.0)
  → Run: pip3 install --upgrade macmon

---

## CR-002: Phase 2 — Universal auto-discovery — COMPLETED 2026-04-22

**Priority:** High
**Status:** Closed

### Change 1 — CR-001: Pre-publish fixes — COMPLETED 2026-04-22

**Priority:** High
**Status:** Closed — all items fixed

### Change 1 — Fix build backend (H-04)
**File:** `pyproject.toml:3`
**Fix:** Changed `setuptools.backends.legacy:build` → `setuptools.build_meta`

### Change 2 — Bind to localhost (C-01)
**File:** `macmon/cli.py:36`
**Fix:** Changed `--host 0.0.0.0` → `--host 127.0.0.1`. Note: `--host` opt-in flag deferred to backlog.

### Change 3 — Remove Google Fonts (H-05)
**File:** `macmon/static/index.html:7-9, 19-20`
**Fix:** Removed 3 Google Fonts `<link>` tags. Updated `--f-sans` and `--f-mono` to system font stack.

### Change 4 — Remove fallback process killer + expand Homebrew map (C-02)
**File:** `macmon/actions.py`
**Fix:** Removed substring fallback killer block. Expanded `_HOMEBREW_SERVICES` to cover all 9 services
that `_BREW_DISPLAY` in metrics.py can surface (added Dolt, PHP, OpenVPN, Unbound, Nginx, MySQL).

### Change 5 — Fix MCP type mismatch (M-06)
**File:** `macmon/metrics.py:364`
**Fix:** Changed filter `s["type"] == "mcp"` → `s["type"] == "mcp-claude"` so MCP recommendations fire.

### Change 6 — Remove personal hardcodes (H-06)
**Files:** `macmon/metrics.py`, `macmon/actions.py`
**Fix:** Removed `NestJS B2B`, `b2b_server`, `clawdbot`, `MCP Supabase`, `MCP Analytics`, `MCP Search Console`
from `_DEV_PATTERNS` and `_AGENT_DISPLAY`. Removed `_NODE_PATTERNS`, `_PYTHON_PATTERNS`, clawdbot from
`_LAUNCH_AGENTS` in actions.py. Removed orphaned `shutil` import.

### Change 7 — Add LICENSE file (H-07)
**File:** `LICENSE` (new)
**Fix:** Standard MIT license, year 2026, Jagan Girisaballa.

### Change 8 — Fix README (H-08)
**File:** `README.md`
**Fix:** Removed broken screenshot image tag. Replaced `pip install macmon` (not on PyPI) with git clone
using correct URL. Added "PyPI coming soon" note.

### Change 9 — Fix GitHub URLs (H-09)
**File:** `pyproject.toml:37-39`
**Fix:** Updated all 3 project URLs from `jagang/macmon` → `jagangirisaballa/macmon`.

---

## CR-002: Phase 2 — Universal auto-discovery

**Priority:** High — must complete before PyPI publish
**Status:** Open

### Overview
Replace all personal hardcodes removed in CR-001 with generic auto-discovery. Goal: any Mac developer
running macmon sees their own services automatically — not a blank panel.

### Change 1 — Node / Bun / Deno server auto-discovery
**File:** `macmon/metrics.py`
**Problem:** `NestJS B2B` hardcode removed. No Node servers shown for anyone now.
**Fix:** Scan all processes whose interpreter is `node`, `bun`, or `deno`. Filter to those that look
like servers: script name matches `server.js`, `main.js`, `app.js`, `index.js`, or a framework binary
(`nest`, `next`, `nuxt`, `vite`, `remix`, `astro`).
**Display name derivation:**
- Framework binary present → use framework name (`nest start` → `"NestJS"`, `next start` → `"Next.js"`)
- Script path present → use parent directory name (`/path/to/my-api/dist/main.js` → `"my-api"`)
- Fallback → `"Node server (PID X)"`
**Stop action:** SIGTERM to PID directly — no named lookup needed.

### Change 2 — MCP server auto-discovery
**File:** `macmon/metrics.py`
**Problem:** 3 MCP hardcodes removed. No MCP servers shown for anyone now.
**Fix:** Scan all processes whose binary starts with `mcp-` or whose command line contains `mcp-server`.
**Display name derivation:** Strip `mcp-server-` or `mcp-` prefix, title-case remainder.
- `mcp-server-supabase` → `"Supabase MCP"`
- `mcp-google-analytics` → `"Google Analytics MCP"`
- Unknown → `"MCP: <binary-name>"`
**Type field:** Emit as `"mcp"` (generic, tool-agnostic). Update metrics.py:364 filter accordingly.
**Stop action:** Advisory only — toggle disabled (MCP servers are child processes of their host tool).

### Change 3 — Python server auto-discovery
**File:** `macmon/metrics.py`
**Problem:** No Python server discovery exists — `_PYTHON_PATTERNS` in actions.py was personal/dead.
**Fix:** Scan processes running under `python`/`python3` or directly as `uvicorn`/`gunicorn`. Filter to
server patterns: uvicorn, gunicorn, flask run, django runserver, fastapi.
**Display name derivation:**
- `uvicorn myapp.server:app` → `"myapp"`
- `gunicorn myproject.wsgi` → `"myproject"`
- `python -m flask run` → `"Flask server"`
- Fallback → `"Python server (PID X)"`
**Stop action:** SIGTERM to PID directly.

### Change 4 — Node/Python stop via PID in actions.py
**File:** `macmon/actions.py`
**Problem:** `_NODE_PATTERNS` and `_PYTHON_PATTERNS` removed. `stop_service` needs a new path for
auto-discovered node/python services that carry a PID but no named map entry.
**Fix:** Add a PID-based stop path. Auto-discovered services will pass their PID in the service record.
`stop_service` checks for a `pid` field and terminates directly if present.

### Change 5 — Recommendation engine: type-based not name-based
**File:** `macmon/metrics.py:330, 340`
**Problem:** Recommendations check for literal names `"MongoDB"`, `"PostgreSQL"`, `"Redis"`, `"NestJS"`.
After auto-discovery, any service type can appear — not just those names.
**Fix:** Reason by type and memory threshold:
- Any `homebrew` service using >50 MB → recommend stopping if swap pressure exists
- Any `node` service using >100 MB and uptime >60 min → recommend stopping if not in active use
- Any `python` service using >100 MB and uptime >60 min → same logic

### Change 6 — Process tagger: expanded dev list
**File:** `macmon/static/index.html:458`
**Problem:** `nest` hardcoded for personal project; list misses most of the Mac dev ecosystem.
**Fix:** Expand to include: `bun`, `deno`, `ruby`, `go`, `java`, `rust`, `cargo`, `mysql`, `redis`,
`nginx`, `docker`, `vite`, `webpack`, `next`, `nuxt`, `rails`, `uvicorn`, `gunicorn`, `mcp`.

### Change 7 — MCP recommendation text: tool-agnostic
**File:** `macmon/metrics.py:371`
**Problem:** Description says "only needed when using Claude Code" — not true for all MCP users.
**Fix:** Change to "only needed when actively using an AI assistant" or similar neutral wording.

---

## Issues deferred to v1.1 (post-publish)

### H-01 — Service control model incomplete
Login-item, app, python, system types not implemented. Frontend shows broken toggles for these.
**Deferred:** Partially addressed by Phase 2 auto-discovery. Full fix in v1.1.

### H-02 — No error handling for missing tools or timeouts
`brew`, `launchctl`, `purge` calls don't catch `FileNotFoundError` or `TimeoutExpired`.
**Deferred:** v1.1

### H-03 — Event loop blocked by synchronous metrics collection
`metrics.collect()` runs `psutil.cpu_percent(interval=0.5)` blocking 500ms in async context.
**Fix when ready:** Move collection into `asyncio.to_thread()`.

### M-01 — Page size hardcoded
Compressed memory calculation hardcodes `16384` bytes/page. Use `os.sysconf('SC_PAGE_SIZE')`.

### M-02 — CPU% per process always shows 0.0
psutil first non-blocking read always returns 0.0. Need PID→sample dict across cycles.

### M-03 — Frontend silently stops updating on malformed payload
`onmessage` swallows all exceptions. Add field guards and visible error state.

### M-04 — Kill button removes row before API confirms success
Row removed optimistically. Wait for API success before DOM removal.

### M-05 — PID file can match a recycled PID
`_is_running()` only checks `kill(pid, 0)`. Store pid + start_time + port in pidfile, verify cmdline.

### L-01 — launchctl load/unload is legacy syntax
Migrate to `bootstrap`/`bootout`/`kickstart` with explicit domain targeting.

### L-02 — Homebrew unavailable makes services disappear silently
`_get_brew_services()` collapses all errors to `{}`. Return availability metadata instead.

### L-03 — Frontend hardcodes http:// and ws://
Derive from `location.origin`. Map `http`→`ws`, `https`→`wss`.
</content>
