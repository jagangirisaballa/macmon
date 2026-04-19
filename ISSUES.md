# macmon — Issue Tracker

> Source: Codex security & production audit — 2026-04-19
> Convert to GitHub Issues on first push.

---

## 🔴 CRITICAL

### [C-01] Dashboard binds to 0.0.0.0 — network exposed
**File:** `macmon/cli.py:36`, `macmon/server.py:53-71`
**Risk:** Anyone on the same WiFi can stop services, kill processes, trigger privileged actions. No auth, no token, no loopback restriction.
**Fix:** Bind to `127.0.0.1` by default. Add `--host` flag for explicit opt-in. Reject non-loopback clients on all mutating endpoints.
**Status:** Open

---

### [C-02] Fallback process killer matches by name substring — wrong process risk
**File:** `macmon/actions.py:87-93`
**Risk:** If a service name isn't in any known type, the fallback does `_find_pids_by_pattern([name.lower()])` and terminates whatever matches — could kill an unrelated process with a similar name.
**Fix:** Remove fallback entirely. Only allow actions against explicitly typed records with stable identifiers (brew_name, launchctl label, PID). Verify target state after action.
**Status:** Open

---

## 🟠 HIGH

### [H-01] Service control model incomplete — login-item, app, python, system types missing
**File:** `macmon/metrics.py:63`, `macmon/metrics.py:220`, `macmon/actions.py:50`, `macmon/static/index.html:413`
**Detail:** Types `login-item` (Vowen, Freeway, Magnet), `app` (Chrome, WhatsApp), `python`, and `system` are not implemented. Frontend shows broken toggles or silent failures for these.
**Fix:** Define one canonical service registry with per-type capabilities (detect, start, stop, read_only, identifier). Make metrics, actions, and frontend all consume same schema.
**Status:** Open

---

### [H-02] No error handling for missing tools or timeouts
**File:** `macmon/actions.py:53`, `:63`, `:105`, `:113`, `:145`, `macmon/server.py:55`
**Detail:** `brew`, `launchctl`, `purge` calls don't catch `FileNotFoundError` or `TimeoutExpired`. If Homebrew isn't installed or a command hangs, the API returns HTTP 500 instead of a structured error.
**Fix:** Wrap every subprocess path. Return normalized JSON errors with distinct causes: `tool_missing`, `timeout`, `permission_denied`, `target_not_found`.
**Status:** Open

---

### [H-03] Event loop blocked by synchronous metrics collection
**File:** `macmon/metrics.py:15`, `:27`, `:129`, `:261`, `macmon/server.py:82`, `:89`
**Detail:** `metrics.collect()` runs `psutil.cpu_percent(interval=0.5)` (blocking 500ms) and a `vm_stat` subprocess inside the async broadcast loop and request handlers. On a slow machine, broadcasts drift and request latency spikes.
**Fix:** Move collection into `asyncio.to_thread()`. Schedule broadcasts against a monotonic deadline instead of `collect(); sleep(2)`.
**Status:** Open

---

### [H-04] Wrong build backend in pyproject.toml
**File:** `pyproject.toml:3`
**Detail:** Uses `setuptools.backends.legacy:build` — this is legacy fallback. Modern setuptools pyproject builds should use `setuptools.build_meta`. `pip install -e .` fails currently.
**Fix:** Switch to `setuptools.build_meta`. Test wheel, sdist, and editable install in a clean venv before PyPI publish.
**Status:** Open

---

### [H-05] Privacy claim contradicted by Google Fonts network call
**File:** `README.md:55`, `macmon/static/index.html:7`
**Detail:** README states "no telemetry / nothing sent anywhere" but the dashboard loads Geist fonts from `fonts.googleapis.com` on every page load — a network request to Google.
**Fix:** Vendor fonts locally inside `macmon/static/fonts/` or fall back to system font stack. Remove Google Fonts link tags.
**Status:** Open

---

## 🟡 MEDIUM

### [M-01] Page size hardcoded — wrong on some Macs
**File:** `macmon/metrics.py:31`
**Detail:** Compressed memory calculation hardcodes `16384` bytes per page. Apple's vm_stat outputs the actual page size in the first line — this varies across hardware/OS versions.
**Fix:** Parse page size from `vm_stat` output first line or use `os.sysconf('SC_PAGE_SIZE')`.
**Status:** Open

---

### [M-02] CPU% per process always shows 0.0
**File:** `macmon/metrics.py:181`, `:239`, `:269`
**Detail:** psutil documents that `cpu_percent()` on the first non-blocking read is always meaningless (returns 0.0 or stale). A prior sample is required.
**Fix:** Maintain a PID→sample dict across collection cycles. Use `Process.cpu_percent(interval=None)` on second+ reads.
**Status:** Open

---

### [M-03] Frontend silently stops updating on malformed payload
**File:** `macmon/static/index.html:345`, `:393`, `:478`, `:600`
**Detail:** `onmessage` catches and swallows all exceptions. If one WebSocket payload has a missing field, the dashboard freezes with no visible error.
**Fix:** Add field guards (`Array.isArray`, null coalescing). Validate payload shape on receipt. Surface render errors visibly in the UI.
**Status:** Open

---

### [M-04] Kill button removes row before API confirms success
**File:** `macmon/static/index.html:539-542`
**Detail:** The process row is removed from the DOM optimistically before the kill API call returns. If the kill fails, the row disappears but the process is still running.
**Fix:** Wait for successful API response before removing row. Always force-refresh after kill regardless of outcome.
**Status:** Open

---

### [M-05] PID file can match a recycled PID
**File:** `macmon/cli.py:14`, `:29`, `:60`
**Detail:** `_is_running()` only checks `kill(pid, 0)`. A stale PID file can match a recycled PID and `macmon stop` could terminate an unrelated process.
**Fix:** Store `pid`, `start_time`, and `port` in PID file. Verify the command line belongs to macmon. Probe HTTP server before trusting PID file.
**Status:** Open

---

### [M-06] MCP type mismatch breaks recommendations
**File:** `macmon/metrics.py:222`, `:364`
**Detail:** Services are emitted as type `mcp-claude` but the recommendations filter checks for type `mcp`. MCP recommendations never trigger.
**Fix:** Normalize the type enum across metrics, recommendations, and frontend.
**Status:** Open

---

## 🔵 LOW

### [L-01] launchctl load/unload is legacy syntax
**File:** `macmon/actions.py:63`, `:113`
**Detail:** `launchctl load/unload` is deprecated. Modern macOS prefers `bootstrap`/`bootout`/`kickstart` with explicit domain targeting.
**Fix:** Migrate to domain-aware commands. Capture stderr/stdout for state diagnostics.
**Status:** Open

---

### [L-02] Homebrew unavailable makes services disappear silently
**File:** `macmon/metrics.py:96`
**Detail:** `_get_brew_services()` collapses all errors to `{}`. If Homebrew isn't installed, the entire Homebrew services section disappears with no explanation.
**Fix:** Return explicit availability/error metadata. Render disabled controls rather than hiding the category.
**Status:** Open

---

### [L-03] Frontend hardcodes http:// and ws:// — breaks behind HTTPS proxy
**File:** `macmon/static/index.html:312-313`
**Detail:** Hardcoded `http://` and `ws://` break if macmon is ever served behind HTTPS or a reverse proxy.
**Fix:** Derive from `location.origin`. Map `http`→`ws`, `https`→`wss` automatically.
**Status:** Open

---

## Summary

| Severity | Count | Blocking |
|---|---|---|
| 🔴 Critical | 2 | Ship to anyone |
| 🟠 High | 5 | PyPI / GitHub publish |
| 🟡 Medium | 6 | Before v1.1 |
| 🔵 Low | 3 | Polish |

**Recommended fix order before first public share:**
C-01 → C-02 → H-05 → H-04 → H-02 → H-01 → H-03
