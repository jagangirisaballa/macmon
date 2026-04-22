# macmon

> Real-time Mac system monitoring dashboard with smart optimization recommendations.

## Features

- **Live metrics** — CPU, RAM, swap, disk updated every 2 seconds
- **Slowdown detection** — 3-tier status (normal / warning / critical) with root cause
- **macOS notifications** — native alerts when your system slows down
- **Dev services panel** — MongoDB, PostgreSQL, Node, Python servers — stop/start with one click
- **Top processes** — see what's eating your RAM, kill with confirmation
- **Smart recommendations** — context-aware suggestions ("MongoDB idle 2h, free 56MB")
- **Start/stop anywhere** — single CLI command, opens browser automatically

## Install

```bash
git clone https://github.com/jagangirisaballa/macmon.git
cd macmon
pip install -e .
```

> PyPI release coming soon — `pip install macmon` will work once published.

**Optional: native notifications**

```bash
brew install terminal-notifier
```

## Usage

```bash
macmon start          # start dashboard, opens http://localhost:9999
macmon start --port 8080   # custom port
macmon stop           # stop the dashboard
macmon status         # check if running
macmon logs           # view recent logs
```

## Requirements

- macOS (Apple Silicon or Intel)
- Python 3.9+
- Homebrew (optional, for service control)

## How it works

macmon runs a lightweight FastAPI server locally. The dashboard connects via WebSocket and receives system metrics every 2 seconds. All data stays on your machine — nothing is sent anywhere.

**Slowdown thresholds (tuned for 8GB M1, adjustable):**
- Warning: swap > 20% OR free RAM < 1 GB
- Critical: swap > 50% OR free RAM < 500 MB

## Contributing

PRs welcome. Open an issue first for major changes.

## License

MIT © Jagan Girisaballa
