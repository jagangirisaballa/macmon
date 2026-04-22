# macmon — Active Backlog

Current version: 1.0.0

## Open CRs

| ID | Title | Priority | Status |
|----|-------|----------|--------|
| CR-002 | Phase 2 — Universal auto-discovery: Node, MCP, Python server scanning | High | **Done 2026-04-22** |
| CR-003 | Tag v1.0.0 release on GitHub | High | Open |
| CR-004 | Add dashboard screenshot to README | High | Open |
| CR-005 | Publish to PyPI | High | Open |
| CR-006 | v1.1 bug fixes — M-01 through M-04, L-01, L-02 | Medium | Open |

---

### CR-003 — Tag v1.0.0 release on GitHub

**Goal:** Create a `v1.0.0` git tag and a GitHub Release so the repo shows "1 release" instead of nothing. Makes the project look finished and gives users a stable reference point.

**Steps:**
1. Create and push the tag:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
2. Go to https://github.com/jagangirisaballa/macmon/releases/new
3. Select tag `v1.0.0`
4. Title: `v1.0.0 — Initial release`
5. Body (release notes):

   ```
   First public release of macmon.

   ## What's included
   - Live CPU, RAM, swap, disk monitoring — updated every 2 seconds
   - Homebrew service stop/start (MongoDB, PostgreSQL, Redis, and more)
   - Auto-discovery of Node, Python, and MCP servers — no configuration needed
   - Smart recommendations with one-click actions
   - Top processes list with kill button
   - macOS native notifications
   - Local only — no telemetry, no internet required

   ## Install
   git clone https://github.com/jagangirisaballa/macmon.git
   cd macmon
   pip install -e .
   macmon start
   ```
6. Click **Publish release**

**Done when:** https://github.com/jagangirisaballa/macmon/releases shows v1.0.0.

---

### CR-004 — Add dashboard screenshot to README

**Goal:** Add a real screenshot of the macmon dashboard to the README. Repos without visuals get significantly less engagement — people want to see what they're installing.

**Steps:**
1. Start macmon: `macmon start`
2. Make sure the dashboard has some live data showing (wait a few seconds)
3. Take a screenshot of the browser window — either:
   - Full browser window: `Cmd + Shift + 4`, then Space, click the browser window
   - Or use macOS screenshot tool: `Cmd + Shift + 5`
4. Save as `docs/screenshot.png`
5. Add to README — insert after the opening paragraph, before "Quick install":
   ```markdown
   ![macmon dashboard](docs/screenshot.png)
   ```
6. Commit and push:
   ```bash
   git add docs/screenshot.png README.md
   git commit -m "docs: add dashboard screenshot"
   git push
   ```

**Done when:** The screenshot is visible on the GitHub repo page.

---

### CR-005 — Publish to PyPI

**Goal:** Publish macmon to PyPI so anyone can install it with `pip install macmon` — no git clone required. This is the single biggest install friction improvement.

**Steps:**

1. **Create a PyPI account** (if you don't have one):
   - Go to https://pypi.org/account/register/
   - Verify your email

2. **Install build tools:**
   ```bash
   pip install build twine
   ```

3. **Build the package:**
   ```bash
   cd /Users/jagang/macmon
   python -m build
   ```
   This creates a `dist/` folder with two files: a `.tar.gz` and a `.whl`.

4. **Upload to PyPI:**
   ```bash
   twine upload dist/*
   ```
   Enter your PyPI username and password when prompted.
   (Recommended: use an API token instead of password — create one at https://pypi.org/manage/account/token/)

5. **Verify it works:**
   ```bash
   pip install macmon
   macmon start
   ```

6. **Update README** — change the install section to lead with pip:
   ```markdown
   ## Quick install
   pip install macmon
   macmon start
   ```
   Keep the `git clone` path as the secondary option for developers who want to modify it.

7. Commit and push the README update.

**Done when:** `pip install macmon` works from a fresh terminal and `macmon start` opens the dashboard.

---

### CR-006 — v1.1 bug fixes

**Goal:** Fix the most visible bugs before the LinkedIn post gets traction and people start filing issues.

**Bugs included (ordered by user impact):**

| Bug | Impact | Fix summary |
|-----|--------|-------------|
| M-02: CPU% always 0.0 | Every user sees this | psutil requires two calls with an interval to get a real CPU% — collect it properly |
| M-04: Kill button removes row before API confirms | UX glitch — row disappears then reappears if kill fails | Only remove row after API returns success |
| M-03: Frontend silently stops on malformed payload | Dashboard freezes with no indication | Wrap JSON parse in try/catch, show reconnect state |
| M-01: Page size hardcoded — wrong compressed memory | Wrong numbers on non-16KB page-size Macs | Read page size dynamically from `vm_stat` output |
| L-02: Homebrew unavailable makes services disappear silently | Services panel goes blank with no explanation | Show a "Homebrew not found" placeholder instead of empty panel |
| L-01: launchctl load/unload is legacy syntax | Deprecation warning on newer macOS | Use `launchctl bootout` / `launchctl bootstrap` |

**Each fix to be audited individually before logging as done.**

## Known Bugs / Issues

| ID | Title | Severity | Status |
|----|-------|----------|--------|
| C-01 | Dashboard binds to 0.0.0.0 — network exposed | Critical | **Fixed 2026-04-22** |
| C-02 | Fallback process killer matches by name substring — wrong process risk | Critical | **Fixed 2026-04-22** |
| H-01 | Service control model incomplete — login-item, app, python, system types missing | High | Open (Phase 2) |
| H-02 | No error handling for missing tools or timeouts in actions.py | High | Open |
| H-03 | Event loop blocked by synchronous metrics collection | High | Open |
| H-04 | Wrong build backend in pyproject.toml | High | **Fixed 2026-04-22** |
| H-05 | Privacy claim contradicted by Google Fonts network call | High | **Fixed 2026-04-22** |
| H-06 | Personal hardcodes (NestJS B2B, clawdbot, MCP servers) — not universal | High | **Fixed 2026-04-22** |
| H-07 | No LICENSE file — GitHub/PyPI badge missing | High | **Fixed 2026-04-22** |
| H-08 | README broken screenshot + pip install macmon fails (not on PyPI) | High | **Fixed 2026-04-22** |
| H-09 | pyproject.toml URLs used wrong GitHub username (jagang vs jagangirisaballa) | High | **Fixed 2026-04-22** |
| M-01 | Page size hardcoded — wrong compressed memory on some Macs | Medium | Open |
| M-02 | CPU% per process always shows 0.0 | Medium | Open |
| M-03 | Frontend silently stops updating on malformed payload | Medium | Open |
| M-04 | Kill button removes row before API confirms success | Medium | Open |
| M-05 | PID file can match a recycled PID | Medium | Open |
| M-06 | MCP type mismatch breaks recommendations | Medium | **Fixed 2026-04-22** |
| L-01 | launchctl load/unload is legacy syntax | Low | Open |
| L-02 | Homebrew unavailable makes services disappear silently | Low | Open |
| L-03 | Frontend hardcodes http:// and ws:// — breaks behind HTTPS proxy | Low | Open |
</content>
</invoke>