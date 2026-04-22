# macmon — Session Log

---

## 2026-04-20 — Branch: main — Version: 1.0.0

### Done
- Diagnosed "connection refused" on server start — root cause was fastapi/uvicorn not installed in Python 3.14 env
- Fixed by installing dependencies with `pip3 install fastapi uvicorn psutil websockets --break-system-packages`
- Server confirmed running on http://localhost:9999
- Ran Codex security & production audit (blocked by read-only sandbox — plan produced, no code written)
- Clarified that Chrome memory (700 MB across 5 renderer processes) cannot be freed without closing tabs — Chrome Task Manager is the right tool
- Clarified that MCP servers orphan after `/exit` because Claude Code doesn't kill child processes on session exit — workaround is Cmd+Q or kill from macmon process list
- Assessed publish-readiness: not ready yet, three blockers identified
- Created CR-001 covering the three pre-publish blockers

### Bugs Fixed
- None (no code changes landed this session — an earlier unintentional edit was fully reverted)

### Files Touched
- `docs/backlog/active.md` (created)
- `docs/backlog/full.md` (created)
- `docs/backlog/parked.md` (created)
- `docs/session-log.md` (created)

### Pending (carried to next session)
- CR-001: Fix pyproject.toml build backend, bind to 127.0.0.1 by default, remove Google Fonts
- All ISSUES.md items (C-01 through L-03) deferred to v1.1 post-publish

---

## 2026-04-22 — Branch: main — Version: 1.0.0

### Done
- Full codebase audit: identified personal bias (NestJS B2B, clawdbot, MCP hardcodes), packaging bugs, security issues
- Adversarial audit of fix plan — caught coverage gap: `_BREW_DISPLAY` had 10 services, `_HOMEBREW_SERVICES` only 3
- Confirmed GitHub username: jagangirisaballa
- Wrote and executed complete Phase 1 pre-publish plan (9 fixes), each audited before execution
- Fix 1 (C-01): `cli.py:36` — `0.0.0.0` → `127.0.0.1`
- Fix 2 (H-04): `pyproject.toml:3` — build backend `legacy` → `setuptools.build_meta`
- Fix 3 (H-05): `index.html` — removed 3 Google Fonts link tags, updated CSS font vars to system stack
- Fix 4 (C-02): `actions.py` — expanded `_HOMEBREW_SERVICES` to 9 entries, removed fallback substring killer
- Fix 5 (M-06): `metrics.py:364` — fixed MCP type filter `"mcp"` → `"mcp-claude"`
- Fix 6 (H-06): `metrics.py` + `actions.py` — removed all personal hardcodes (NestJS B2B, clawdbot, 3 MCP entries, _NODE_PATTERNS, _PYTHON_PATTERNS, unused shutil import)
- Fix 7 (H-08): `README.md` — removed broken screenshot, fixed install instructions, correct GitHub URL
- Fix 8 (H-07): `LICENSE` — created MIT license file (2026, Jagan Girisaballa)
- Fix 9 (H-09): `pyproject.toml` — corrected all 3 URLs from `jagang` → `jagangirisaballa`
- Designed full Phase 2 plan (CR-002): universal Node/MCP/Python auto-discovery — not yet executed
- Updated memory files with project context, user profile, and plan status

### Bugs Fixed
- C-01: Dashboard network exposure (0.0.0.0 bind)
- C-02: Fallback process killer (substring match — could kill wrong process)
- H-04: Wrong pyproject.toml build backend
- H-05: Google Fonts privacy contradiction
- H-06: Personal hardcodes making app non-universal
- H-07: Missing LICENSE file
- H-08: Broken README screenshot + broken pip install instruction
- H-09: Wrong GitHub username in pyproject.toml URLs
- M-06: MCP type mismatch causing recommendations to never fire

### Files Touched
- `macmon/cli.py`
- `macmon/server.py` (verified — already correct, no change needed)
- `macmon/metrics.py`
- `macmon/actions.py`
- `macmon/static/index.html`
- `pyproject.toml`
- `README.md`
- `LICENSE` (created)
- `docs/backlog/active.md`
- `docs/backlog/full.md`
- `docs/backlog/parked.md`
- `docs/session-log.md`
- `.claude/projects/.../memory/MEMORY.md` (created)
- `.claude/projects/.../memory/user_profile.md` (created)
- `.claude/projects/.../memory/project_context.md` (created)
- `.claude/projects/.../memory/plan_prepublish.md` (created)

### Pending (carried to next session)
- Push to GitHub (repo not yet created — create at github.com/jagangirisaballa/macmon first)
- H-01, H-02, H-03, M-01 through M-05, L-01 through L-03 — all deferred to v1.1

---

## 2026-04-22 (session 2) — Branch: main — Version: 1.0.0

### Done — Phase 2 (CR-002): Universal auto-discovery — COMPLETE

Each step audited against plan before being logged.

**Step 1 — Dead code removal:**
- Deleted orphaned `_SERVICE_PATTERNS` (metrics.py lines 63-74, never used after Phase 1)

**Step 2 — MCP server auto-discovery (metrics.py `_get_services`):**
- Scans all processes for `/.bin/mcp-` or `/mcp-server-` in cmdline
- Skips npm exec wrapper processes (only matches real node worker)
- Derives display name from path segment (e.g. `mcp-server-supabase` → "MCP Supabase")
- Appends `--project-ref` prefix (8 chars) when multiple instances of same server exist
- Type: `"mcp-claude"` — consistent with existing frontend/rec checks
- Audit: confirmed 4 MCP workers discovered (GSC, Google Analytics, 2× Supabase with project-refs)

**Step 3 — Node/Bun/Deno dev server auto-discovery (metrics.py `_get_services`):**
- Matches processes named `node`, `bun`, `deno`
- Excludes `/.npm/_npx/` cache paths (MCP wrappers/one-off tools)
- Requires known dev server signal: `npm start`, `npm run`, `ng serve`, `next`, `vite`, `nest start`, `ts-node`, `nodemon`, `tsx`
- Skips children whose parent PID is already matched (prevents ng serve showing under npm start)
- Derives display name from `package.json#name` in process CWD, fallback to script filename
- Type: `"node"`
- Audit: confirmed `superGryd` discovered via package.json; ng serve child correctly suppressed

**Step 4 — Python server auto-discovery (metrics.py `_get_services`):**
- Matches `uvicorn `, `gunicorn `, `flask run`, `manage.py runserver` in cmdline
- Derives display name from app module arg (e.g. `uvicorn macmon.server:app` → "macmon")
- Type: `"python"`

**Step 5 — PID-based stop (actions.py + server.py + index.html):**
- Added `stop_pid(pid)` to actions.py — delegates to `kill_process`
- Added `POST /api/service/stop-pid/{pid}` route to server.py
- Frontend toggle: embeds `data-svc-pid` for node/python/mcp-claude services
- Frontend toggle click handler: routes to stop-pid endpoint when pid present and running
- Recommendations click handler: `stop_pid` action routes to `/api/service/stop-pid/{target}`

**Step 6 — Recommendation engine: type-based (metrics.py `_get_recommendations`):**
- Homebrew recs: `svc["type"] == "homebrew"` replaces name list (`"MongoDB"`, `"PostgreSQL"`, `"Redis"`)
- Node/Python recs: `svc["type"] in ("node", "python") and uptime > 60 and mem > 30`
- Node/Python rec action: `"stop_pid"` with PID as target (not name)
- `"NestJS"` name-check removed

**Step 7 — MCP recommendation text (metrics.py):**
- Removed "Claude Code" reference: `"only needed when using Claude Code"` → `"stop if not actively using these tools to free RAM"`

**Bonus fixes during audit:**
- `import json as _json` inside function moved to top-level imports
- Footer GitHub URL in index.html fixed: `jagang` → `jagangirisaballa` (missed in Phase 1)

### Audit results — all 7 steps PASS
- `_SERVICE_PATTERNS` deleted: confirmed
- `mcp-claude` type string consistent across all 4 locations: confirmed
- No stale `"mcp"` type strings: confirmed
- No Electron/app processes leaked into services panel: confirmed
- `collect()` runs clean, all types correct: confirmed

### Files Touched
- `macmon/metrics.py` — Steps 1–7
- `macmon/actions.py` — Step 5 (stop_pid)
- `macmon/server.py` — Step 5 (stop-pid route)
- `macmon/static/index.html` — Steps 5+6 (toggle routing, process tagger, footer URL fix)
- `docs/session-log.md`
- `docs/backlog/active.md`

### Pending (carried to next session)
- Push to GitHub (repo not yet created — create at github.com/jagangirisaballa/macmon first)
- H-01, H-02, H-03, M-01 through M-05, L-01 through L-03 — all deferred to v1.1

---

## 2026-04-22 (session 3) — Branch: main — Version: 1.1.3

### Done
- Full audit of all Phase 1 + Phase 2 changes — 4 issues found and fixed (mcp-claude dead code in pidTypes, _find_pids_by_pattern dead code, unused pname variable, double blank line)
- README completely rewritten — structured for both developers and non-developers
- CR-003: Tagged v1.0.0 and created GitHub Release (manual — user did in browser)
- CR-004: Dashboard screenshot taken, saved to docs/screenshot.png, added to README
- CR-005: PyPI account created, macmon published — `pip3 install macmon` now works
- CR-006: All 6 v1.1 bugs fixed (M-01 page size, M-02 CPU%, M-03 payload guard, M-04 kill button, L-01 launchctl syntax, L-02 Homebrew missing warning)
- CR-007: GitHub Actions release workflow — tag push now auto-publishes to PyPI + creates GitHub Release
- CR-008: Stop button added to dashboard header — `/api/shutdown` endpoint added to server.py
- CR-009 (critical): Fixed macmon stop — was only killing PID file process, leaving orphans running and sending notifications after stop. Now scans all uvicorn macmon.server processes and kills them all.
- CR-010: Update check on `macmon start` — prints notice + upgrade command if newer version on PyPI
- README troubleshooting updated — notification bug, update command, externally-managed-environment error
- LinkedIn post published — https://www.linkedin.com/posts/jagan-girisaballa_opensource-buildinpublic-developertools-share-7452610562791841792-w2qx
- Verified `pip3 install macmon` works end-to-end in a fresh venv
- All versions bumped and published: 1.0.0 → 1.1.0 → 1.1.1 → 1.1.2 → 1.1.3

### Bugs Fixed
- M-01: Compressed memory page size hardcoded — now read dynamically from vm_stat header
- M-02: CPU% always 0.0 — psutil baseline seeded at module load
- M-03: Frontend silent stop on malformed payload — shape guard added before renderAll
- M-04: Kill button removes row before API confirms — now waits for success response
- L-01: launchctl legacy syntax — migrated to bootout/bootstrap with gui/{uid} domain
- L-02: Homebrew missing = blank panel — shows "Homebrew not found" warning entry
- M-05 (partial): macmon stop PID file mismatch — full process scan now used (CR-009)
- Audit finds: mcp-claude in pidTypes dead code, _find_pids_by_pattern dead code, unused pname in Python scanner, double blank line in server.py — all removed

### Files Touched
- `macmon/metrics.py` — M-01, M-02, M-03, L-02, import re/shutil added
- `macmon/actions.py` — L-01 launchctl syntax, import os added, dead code removed
- `macmon/server.py` — CR-008 shutdown endpoint, version bumps
- `macmon/cli.py` — CR-009 full process scan stop, CR-010 update check
- `macmon/static/index.html` — M-04 kill button fix, stop button, version bumps
- `macmon/__init__.py` — version bumps
- `pyproject.toml` — version bumps
- `README.md` — full rewrite + pip install + troubleshooting + update docs
- `docs/screenshot.png` — created
- `docs/backlog/active.md` — all CRs and bugs updated
- `docs/backlog/full.md` — CR-007 through CR-010 specs added
- `docs/session-log.md` — this entry
- `.github/workflows/release.yml` — created

### Pending (carried to next session)
- H-01: Service control model incomplete — login-item, app, python, system types
- H-02: No error handling for missing tools or timeouts in actions.py
- H-03: Event loop blocked by synchronous metrics collection
- L-03: Frontend hardcodes http:// and ws:// — breaks behind HTTPS proxy
- Monitor LinkedIn post for feature requests / bug reports and log as CRs
- Consider pipx as recommended install path (cleaner than --break-system-packages)
