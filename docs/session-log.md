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
