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
- CR-002: Phase 2 — Universal auto-discovery (Node/Bun/Deno, MCP, Python servers)
  - Node/Bun/Deno server scanner with display name derivation
  - MCP server scanner (generic mcp-* process scan)
  - Python server scanner (uvicorn/gunicorn/flask/django)
  - PID-based stop in actions.py (replaces named pattern lookup)
  - Recommendation engine: type-based not name-based
  - Process tagger: expanded dev list in index.html
  - MCP recommendation text: remove "Claude Code" reference
- Push to GitHub (repo not yet created — create at github.com/jagangirisaballa/macmon first)
- H-01, H-02, H-03, M-01 through M-05, L-01 through L-03 — all deferred to v1.1
