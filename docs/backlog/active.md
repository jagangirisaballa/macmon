# macmon — Active Backlog

Current version: 1.0.0

## Open CRs

| ID | Title | Priority | Status |
|----|-------|----------|--------|
| CR-001 | Pre-publish fixes: install story, localhost bind, remove Google Fonts | High | Open |

## Known Bugs / Issues (from ISSUES.md audit)

| ID | Title | Severity | Status |
|----|-------|----------|--------|
| C-01 | Dashboard binds to 0.0.0.0 — network exposed | Critical | Open (in CR-001) |
| C-02 | Fallback process killer matches by name substring — wrong process risk | Critical | Open |
| H-01 | Service control model incomplete — login-item, app, python, system types missing | High | Open |
| H-02 | No error handling for missing tools or timeouts in actions.py | High | Open |
| H-03 | Event loop blocked by synchronous metrics collection | High | Open |
| H-04 | Wrong build backend in pyproject.toml | High | Open (in CR-001) |
| H-05 | Privacy claim contradicted by Google Fonts network call | High | Open (in CR-001) |
| M-01 | Page size hardcoded — wrong on some Macs | Medium | Open |
| M-02 | CPU% per process always shows 0.0 | Medium | Open |
| M-03 | Frontend silently stops updating on malformed payload | Medium | Open |
| M-04 | Kill button removes row before API confirms success | Medium | Open |
| M-05 | PID file can match a recycled PID | Medium | Open |
| M-06 | MCP type mismatch breaks recommendations | Medium | Open |
| L-01 | launchctl load/unload is legacy syntax | Low | Open |
| L-02 | Homebrew unavailable makes services disappear silently | Low | Open |
| L-03 | Frontend hardcodes http:// and ws:// — breaks behind HTTPS proxy | Low | Open |
