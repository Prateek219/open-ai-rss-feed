

A lightweight CLI tool to monitor OpenAI's status feed in real-time and query incident history.

## Installation

```bash
pip install aiohttp feedparser loguru
```

## Usage

```bash
python bolna_pulse.py <command>
```

### Commands

| Command | Description |
|---|---|
| `listen` | Start real-time monitoring (polls every 60s) |
| `all` | Show all stored incidents |
| `pulse` | Check system heartbeat |
| `range <start> <end>` | Filter incidents by date range (`DDMMYYYY`) |
| `filter <color>` | Filter by severity: `green`, `yellow`, or `red` |

### Examples

```bash
# Start live monitoring
python bolna_pulse.py listen

# View all incidents
python bolna_pulse.py all

# Incidents between Jan 1–31, 2025
python bolna_pulse.py range 01012025 31012025

# Show only critical incidents
python bolna_pulse.py filter red
```

## Severity Levels

| Color | Meaning | Triggered by keywords |
|---|---|---|
| 🔴 `red` | Outage / Critical | `down`, `outage`, `critical` |
| 🟡 `yellow` | Degraded Performance | `latency`, `degraded`, `issue` |
| 🟢 `green` | Operational | *(default)* |

## Data

Incidents are stored locally in `status_history.json` — no database required.
