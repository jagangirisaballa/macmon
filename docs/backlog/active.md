# macmon — Active Backlog

Current version: 1.1.3

## Open CRs

| ID | Title | Priority | Status |
|----|-------|----------|--------|
| CR-002 | Phase 2 — Universal auto-discovery: Node, MCP, Python server scanning | High | **Done 2026-04-22** |
| CR-003 | Tag v1.0.0 release on GitHub | High | **Done 2026-04-22** |
| CR-004 | Add dashboard screenshot to README | High | **Done 2026-04-22** |
| CR-005 | Publish to PyPI | High | **Done 2026-04-22** |
| CR-006 | v1.1 bug fixes — M-01 through M-04, L-01, L-02 | Medium | **Done 2026-04-22** |
| CR-007 | GitHub Actions automated release workflow | High | **Done 2026-04-22** |
| CR-008 | Stop button in dashboard header + /api/shutdown endpoint | Medium | **Done 2026-04-22** |
| CR-009 | macmon stop kills all procs not just PID file | Critical | **Done 2026-04-22** |
| CR-010 | Update check on macmon start | Medium | **Done 2026-04-22** |

## Known Bugs / Issues

| ID | Title | Severity | Status |
|----|-------|----------|--------|
| C-01 | Dashboard binds to 0.0.0.0 — network exposed | Critical | **Fixed 2026-04-22** |
| C-02 | Fallback process killer matches by name substring — wrong process risk | Critical | **Fixed 2026-04-22** |
| H-01 | Service control model incomplete — login-item, app, python, system types missing | High | Open |
| H-02 | No error handling for missing tools or timeouts in actions.py | High | Open |
| H-03 | Event loop blocked by synchronous metrics collection | High | Open |
| H-04 | Wrong build backend in pyproject.toml | High | **Fixed 2026-04-22** |
| H-05 | Privacy claim contradicted by Google Fonts network call | High | **Fixed 2026-04-22** |
| H-06 | Personal hardcodes (NestJS B2B, clawdbot, MCP servers) — not universal | High | **Fixed 2026-04-22** |
| H-07 | No LICENSE file — GitHub/PyPI badge missing | High | **Fixed 2026-04-22** |
| H-08 | README broken screenshot + pip install macmon fails (not on PyPI) | High | **Fixed 2026-04-22** |
| H-09 | pyproject.toml URLs used wrong GitHub username (jagang vs jagangirisaballa) | High | **Fixed 2026-04-22** |
| M-01 | Page size hardcoded — wrong compressed memory on some Macs | Medium | **Fixed 2026-04-22** |
| M-02 | CPU% per process always shows 0.0 | Medium | **Fixed 2026-04-22** |
| M-03 | Frontend silently stops updating on malformed payload | Medium | **Fixed 2026-04-22** |
| M-04 | Kill button removes row before API confirms success | Medium | **Fixed 2026-04-22** |
| M-05 | PID file can match a recycled PID / macmon stop misses orphan procs | Medium | **Fixed 2026-04-22** |
| M-06 | MCP type mismatch breaks recommendations | Medium | **Fixed 2026-04-22** |
| L-01 | launchctl load/unload is legacy syntax | Low | **Fixed 2026-04-22** |
| L-02 | Homebrew unavailable makes services disappear silently | Low | **Fixed 2026-04-22** |
| L-03 | Frontend hardcodes http:// and ws:// — breaks behind HTTPS proxy | Low | Open |
</content>
</invoke>