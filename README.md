English | [Chinese](README_ZH.md)

---

# Server-Mate | Lightweight Server Monitoring and AI Ops

> A two-plane monitoring system for Linux hosts running Nginx or Apache.

[![Version](https://img.shields.io/badge/version-1.3.2-blue.svg)]()
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-success.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-CentOS%2FUbuntu%2FDebian-lightgrey.svg)](https://linux.org)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Web Server](https://img.shields.io/badge/Web%20Server-Nginx%2FApache-orange.svg)](https://nginx.org)

---

## Overview

**Server-Mate** is a lightweight server monitoring and AI operations workflow for Linux web hosts running Nginx or Apache.

It splits responsibilities into two planes:
- **Server Agent**: a Python collector that tails logs, samples host metrics, and writes SQLite rollups
- **AI Analyzer**: an OpenClaw-side layer that generates reports, pushes webhooks, explains issues, and drives guarded automation

### Key Features

- **Real-time metrics**: CPU, memory, disk, load, and network I/O via `psutil`
- **Log parsing**: normalized Nginx and Apache access/error log processing
- **Traffic analytics**: PV, UV, IP count, QPS, bandwidth, and status-code breakdowns
- **Spider detection**: crawler-family recognition and traffic separation
- **Smart alerts**: DingTalk, WeCom, Feishu, and Telegram webhook delivery
- **SSH Security Shield**: auth-log brute-force detection linked to auto-ban
- **AI diagnosis**: plain-language explanations and remediation guidance
- **Auto reports**: daily, weekly, and monthly PDF reports with AI commentary
- **SSL expiry checks**: certificate remaining days in PDF summaries and webhook messages
- **Guarded Automation**: optional auto-ban and auto-heal with cooldowns, allowlists, and audit logs

### Use Cases

- Add observability to Linux hosts without replacing your current stack
- Get AI-powered explanations instead of reading raw logs line by line
- Generate daily, weekly, and monthly ops reports automatically
- Detect suspicious IPs, 404 scans, 5xx spikes, and SSH brute-force attempts
- Enable safe automation with allowlists, TTLs, cooldowns, and audit trails

---

## What's New in v1.3.2

### SSH Security Shield

- **Auth log parsing**: incrementally parses `logs.auth_log`, or auto-detects `/var/log/auth.log` and `/var/log/secure`, for `Failed password` fingerprints
- **Linked auto-ban**: repeated SSH failures raise `ssh_brute_force` alerts and can flow into the existing whitelist-aware auto-ban pipeline

### SSL Expiry Checker

- **Certificate inspection**: report generation now checks each configured site certificate with Python `ssl` and `socket`
- **Visible everywhere**: remaining days appear in PDF overview blocks and webhook markdown summaries, with warning markers below 15 days

### PDF Overflow Guard

- **URL / Referer truncation**: query strings are removed before table rendering, then long text is hard-truncated
- **Stable table layouts**: oversized tokens no longer break dense PDF pages

### Telegram Push

- **New channel**: the webhook center now supports Telegram bot delivery
- **Environment fallback**: `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are used when config values are empty

### Out-of-the-box GeoIP

- **Auto-provisioning**: the report generator automatically downloads the required GeoLite2 `.mmdb` database from a public mirror if it is missing
- **MaxMind-first workflow**: if `./data/GeoIP.conf` exists and `geoipupdate` is installed, Server-Mate refreshes GeoLite2 from your own MaxMind account before falling back to the public mirror

### AI Alert Diagnosis

- **Pre-send AI review**: warning and critical alerts can call the shared AI endpoint before webhook delivery
- **Two-sentence output**: alert cards append a compact `AI Diagnosis` block with plain-language cause and next action

### systemd Template

- **`--generate-service`**: the agent can print a host-local systemd unit template for daemon hosting with `Restart=always`

### Multi-Site Monitoring

- **Matrix configuration**: monitor multiple domains on the same host with a `sites[]` array
- **System metrics**: dedicated `system_metrics` settings for host-global resources
- **Scope separation**: host-global metrics are separated from site-local traffic rollups via `__host__`

### Hardened Log Reading

- **Logrotate support**: handles inode changes, file truncation, and temporary file absence
- **Incremental reading**: robust state tracking across log rotations and restarts

### Guarded Automation

- **Dry-run mode**: test automation policies before enabling real actions
- **Whitelist-aware auto-ban**: protects trusted IPs and known spiders
- **TTL-based unban**: automatic unban after configurable TTL
- **Cooldown protection**: prevents action storms with per-rule cooldowns
- **Mandatory notifications**: all automation actions are logged and notified

### SQLite Audit Tracking

- **`automation_actions` table**: complete audit trail of automation events
- **`banned_ips` table**: tracks active bans with TTL and metadata

### Configuration

- **`config.example.yaml`**: recommended starting point for v1.3.2 with multi-site, Telegram, SSH auth monitoring, SSL checks, AI diagnosis, and Guarded Automation pre-configured

---

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/tankeito/server-mate.git
cd server-mate

# Install dependencies
python3 -m pip install psutil pyyaml matplotlib

# Optional: GeoIP support
python3 -m pip install geoip2 maxminddb aiohttp

# Optional: official MaxMind updater
# CentOS / Rocky / AlmaLinux: sudo yum install geoipupdate
# Ubuntu / Debian: sudo apt-get install geoipupdate
```

### 2. Configuration

Start by copying [`config.example.yaml`](config.example.yaml) to `config.yaml`.

In OpenClaw, keep `config.yaml`, `metrics.db`, `logs/`, and `reports/` inside the current workspace, meaning under `./`, instead of writing into global system directories.

If AI features are enabled, OpenClaw injects `OPENAI_API_KEY` automatically, so you do not need to run `export OPENAI_API_KEY=...` manually.

```yaml
agent:
  host_id: web-01
  timezone: Asia/Shanghai
  mode: once

system_metrics:
  enabled: true

logs:
  auth_log: ""

sites:
  - domain: site-a.example.com
    site_host: site-a.example.com
    enabled: true
    access_log: ./logs/site-a.access.log
    error_log: ./logs/site-a.error.log
  - domain: site-b.example.com
    site_host: site-b.example.com
    enabled: true
    access_log: ./logs/site-b.access.log
    error_log: ./logs/site-b.error.log

storage:
  database_file: ./metrics.db
  rollup_minutes: [10, 60]

notifications:
  webhooks:
    dingtalk:
      enabled: true
      url: https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN
    telegram:
      enabled: false
      bot_token: ""
      chat_id: ""
  reports:
    report_language: zh
    report_export_dir: ""
    public_base_url: ""
    geoip_city_db: ./data/GeoLite2-City.mmdb
    geoip_update_config: ./data/GeoIP.conf
    ai_analysis:
      enabled: true
      simulate: false
      api_key_env: OPENAI_API_KEY
    daily:
      enabled: true
      push_time: "08:30"
      channels: [dingtalk]
      output_dir: ./reports

automation:
  dry_run: true
  auto_ban:
    enabled: false
  auto_heal:
    enabled: false
```

### 2.1 GeoIP Notes

- Put your MaxMind config at `./data/GeoIP.conf`
- Create `./data/GeoIP.conf` manually and keep the real file out of Git
- Install `geoip2` and its supporting packages such as `maxminddb` and `aiohttp` if you want real region lookups in reports
- Free GeoLite2 account: [MaxMind GeoLite sign up](https://www.maxmind.com/en/geolite2/signup)
- License key guide: [Generate a License Key](https://support.maxmind.com/hc/en-us/articles/4407111582235-Generate-a-License-Key)
- `geoip_update_config` is optional, but `./data/GeoIP.conf` is the recommended local path
- If you do not want to use MaxMind directly, Server-Mate still falls back to the public `.mmdb` mirror
- If a MaxMind key was ever exposed in plain text, rotate it before production use

### 3. Run Agent Manually

```bash
# One-shot collection
python3 scripts/server_agent.py --config config.yaml --once

# View collected rollups
python3 scripts/report_generator.py --config config.yaml daily --date 2026-03-26 --json
```

### 4. Schedule with Cron

```bash
crontab -e
```

Add these lines:

```cron
# Data collection every 10 minutes
*/10 * * * * /usr/bin/env bash -lc 'python3 ./scripts/server_agent.py --config ./config.yaml --once >> ./logs/server-mate-agent.log 2>&1'

# Daily PDF report at 01:00
0 1 * * * /usr/bin/env bash -lc 'python3 ./scripts/report_generator.py --config ./config.yaml pdf --range daily --send >> ./logs/server-mate-report.log 2>&1'

# Weekly PDF report every Monday at 01:10
10 1 * * 1 /usr/bin/env bash -lc 'python3 ./scripts/report_generator.py --config ./config.yaml pdf --range weekly --send >> ./logs/server-mate-report.log 2>&1'

# Monthly PDF report on the 1st at 01:20
20 1 1 * * /usr/bin/env bash -lc 'python3 ./scripts/report_generator.py --config ./config.yaml pdf --range monthly --send >> ./logs/server-mate-report.log 2>&1'
```

---

## Architecture

### Two-Plane Design

```text
+--------------------------------------------------------------+
| Server Agent (Linux Host)                                    |
| - psutil metrics (CPU / memory / disk / network)             |
| - Incremental log reading (Nginx / Apache access + error)    |
| - JSON event emission                                        |
| - SQLite rollup writing                                      |
+--------------------------------------------------------------+
                            |
                            | SQLite / JSON events
                            v
+--------------------------------------------------------------+
| AI Analyzer (OpenClaw)                                       |
| - Aggregation and storage                                    |
| - Natural-language query handling                            |
| - AI error diagnosis                                         |
| - Webhook delivery (DingTalk / WeCom / Feishu / Telegram)    |
| - Guarded auto-ban / auto-heal                               |
| - PDF report generation (daily / weekly / monthly)           |
+--------------------------------------------------------------+
```

### Component Flow

1. **Agent collection**: generates `system_snapshot`, `access_event`, and `error_event`
2. **SQLite rollups**: writes 10-minute and 60-minute buckets
3. **Report generator**: reads rollups and generates PDF or Markdown output
4. **Webhook center**: sends alerts and report summaries
5. **AI analysis**: optionally calls an LLM for explanations and recommendations

---

## Data Contracts

### Core Event Types

| Event Type | Purpose | Key Fields |
|------------|---------|------------|
| `system_snapshot` | Host health metrics | `cpu_pct`, `memory_pct`, `disk_free_bytes`, `load_1m` |
| `access_event` | Parsed access log | `client_ip`, `uri`, `status`, `response_ms`, `user_agent` |
| `error_event` | Parsed error log | `severity`, `component`, `category`, `fingerprint`, `message` |
| `action_event` | Audit trail | `action`, `target`, `reason`, `dry_run`, `result`, `ttl_seconds` |

### Metric Definitions

| Metric | Definition |
|--------|------------|
| **PV** | Total request count in the selected window |
| **UV** | Unique visitor key, typically IP plus user-agent fallback |
| **IP Count** | Unique client IPs |
| **QPS** | `request_count / window_seconds` |
| **Slow Request** | `response_ms > threshold`, default `2000ms` |
| **Bandwidth Out** | Sum of response bytes |

---

## Configuration Reference

### `agent` Section

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `host_id` | string | - | Logical host name for alerts and reports |
| `timezone` | string | `UTC` | Local timezone for bucket scheduling |
| `mode` | string | `once` | `once` or `daemon` |
| `poll_interval_seconds` | int | `60` | Agent loop interval in daemon mode |
| `state_file` | string | `./server_agent_state.json` | Cursor state file for incremental reading |

### `system_metrics` Section

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | `true` | Whether to collect host-global metrics |
| `disk_root` | string | `/` | Mount point used for disk checks |
| `collect_network_io` | boolean | `true` | Whether to collect network I/O |

### `logs` Section

| Field | Type | Description |
|-------|------|-------------|
| `auth_log` | string | SSH auth log path; auto-detected if empty |

### `sites` Section

| Field | Type | Description |
|-------|------|-------------|
| `domain` | string | Site domain used for report naming and SSL checks |
| `site_host` | string | Display name for the site |
| `enabled` | boolean | Whether this site is enabled |
| `access_log` | string | Access log path |
| `error_log` | string | Error log path |

### `storage` Section

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `database_file` | string | `./metrics.db` | SQLite database path |
| `rollup_minutes` | array | `[10, 60]` | Rollup bucket granularities |

### `notifications.webhooks` Section

| Channel | Fields |
|---------|--------|
| `dingtalk` | `enabled`, `url`, `timeout_seconds`, `at_all` |
| `wecom` | `enabled`, `url`, `timeout_seconds` |
| `feishu` | `enabled`, `url`, `timeout_seconds` |
| `telegram` | `enabled`, `bot_token`, `chat_id`, `timeout_seconds` |

### `notifications.reports` Section

| Field | Type | Description |
|-------|------|-------------|
| `report_language` | string | `zh` or `en` |
| `report_export_dir` | string | Export directory exposed externally for PDFs |
| `public_base_url` | string | URL prefix for report download links |
| `geoip_city_db` | string | GeoLite2 City database path |
| `geoip_update_config` | string | MaxMind updater config path |
| `daily.enabled` | boolean | Enable daily reports |
| `daily.push_time` | string | `"08:30"` format |
| `weekly.push_weekday` | int | `1-7`, where `1` means Monday |
| `monthly.push_day` | int | `1-28` |

### `automation` Section

| Field | Type | Description |
|-------|------|-------------|
| `dry_run` | boolean | When `true`, actions are logged and notified but not executed |
| `auto_ban.enabled` | boolean | Enables automatic banning |
| `auto_ban.whitelist_ips` | array | IP allowlist |
| `auto_ban.ban_ttl_seconds` | int | Ban TTL before automatic release |
| `auto_heal.enabled` | boolean | Enables automatic healing |
| `auto_heal.cooldown_seconds` | int | Cooldown between service restarts |

---

## Report Types

### Daily Report

**Generated**: every day at configured `push_time`

**Contents**:
- PV, UV, and IP totals for the prior 24 hours
- Top pages with PV/UV columns, top IPs with region, and top referers
- Spider traffic breakdown
- Status-code distribution (`2xx`, `3xx`, `4xx`, `5xx`)
- Top errors and slow endpoints
- AI health commentary, if enabled

### Weekly Report

**Generated**: every Monday at the configured time

**Contents**:
- 7-day traffic trend
- Blocked IP trends
- Crawler traffic patterns
- Suspicious route clusters
- Recurring error fingerprints
- AI weekly summary

### Monthly Report

**Generated**: on the 1st of each month

**Contents**:
- 30-day traffic and performance trend
- Disk growth analysis
- Bandwidth peak detection
- Capacity warnings
- Remediation summary
- AI monthly review

---

## Alert Thresholds

| Alert Type | Default Threshold | Window |
|------------|-------------------|--------|
| CPU High | `> 85%` | 5 consecutive minutes |
| Memory High | `> 85%` | 5 consecutive minutes |
| Disk Low | `< 10%` free | Instant |
| 5xx Burst | `> 20` errors | 1 minute |
| Suspicious IP | `> 200` RPM | 1 minute |
| 404 Scan Burst | Sudden spike | Short window |
| Slow Routes | `> 2000ms` average | Alert window |

---

## Safety and Automation

### Auto-Ban Policy (Opt-In)

**Requirements**:
- Allowlist support for trusted IPs
- Clear evidence of abuse, not just flash crowds
- Cooldown and per-hour action caps
- TTL, for example 24 hours
- Audit records with exact commands

**Good Candidates**:
- Repeated request-rate breaches from one IP
- Scanner-like user-agents with 404 spray patterns
- Brute-force hits against admin routes

### Auto-Heal Policy (Conservative)

**Requirements**:
- Repeated `502` or upstream-failure evidence
- Failing health checks or a second confirming signal
- One restart attempt per cooldown window
- Post-action verification
- Escalation path when restart fails

**Preferred Sequence**:
1. Alert
2. Dry-run recommendation
3. One guarded restart of a proven failing service
4. Re-check error rate and service health
5. Escalate instead of looping forever

---

## Project Structure

```text
server-mate/
├── SKILL.md                    # Skill definition and triggers
├── README.md                   # English documentation
├── README_ZH.md                # Chinese documentation
├── user-guide.md               # Detailed deployment guide
├── config.example.yaml         # Full example config template
├── agents/
│   └── openai.yaml             # OpenAI agent interface config
├── references/
│   ├── architecture.md         # System design and component boundaries
│   ├── data-contracts.md       # Event schemas and metric definitions
│   ├── ops-playbook.md         # Thresholds, alerts, and automation policies
│   └── sqlite-schema.md        # Database schema and query patterns
├── scripts/
│   ├── server_agent.py         # Main collector daemon
│   ├── report_generator.py     # PDF and Markdown report generator
│   └── webhook_center.py       # Webhook delivery service
└── config.yaml                 # Runtime configuration file
```

---

## Troubleshooting

### Chinese Text Shows as Squares in PDFs

**Solution**:

```bash
# CentOS / Rocky / AlmaLinux
sudo yum install google-noto-sans-cjk-ttc-fonts

# Ubuntu / Debian
sudo apt-get update
sudo apt-get install fonts-noto-cjk

# Refresh font cache
fc-cache -fv
```

### Webhook Message Contains Only a Local Path

**Solution**:
1. Set `report_export_dir` in config
2. Set `public_base_url` in config
3. Expose the export directory through Nginx or Apache

### No Report Data Appears

**Solution**:
1. Verify the `database_file` path
2. Confirm the agent is writing rollups
3. Confirm the configured site identifiers match the stored data scopes

### Slow Routes or Abnormal IP Sections Are Empty

**Solution**:
- Make sure the current agent version has created `slow_request_rollups` and `suspicious_ip_rollups` tables

---

## Support

- **GitHub Issues**: https://github.com/tankeito/server-mate/issues
- **Repository**: https://github.com/tankeito/server-mate
- **Email**: tqd354@gmail.com

---

**Server-Mate** | Lightweight Server Monitoring and AI Ops

**Developed by tankeito** | MIT License | 2026
