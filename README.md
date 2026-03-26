English | [中文](README_ZH.md)

---

# 🖥️ Server-Mate | Lightweight Server Monitoring & AI Ops

> A two-plane monitoring system for Linux hosts running Nginx or Apache.

[![Version](https://img.shields.io/badge/version-1.1.2-blue.svg)]()
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-success.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-CentOS%2FUbuntu%2FDebian-lightgrey.svg)](https://linux.org)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Web Server](https://img.shields.io/badge/Web%20Server-Nginx%2FApache-orange.svg)](https://nginx.org)

---

## 📖 Overview

**Server-Mate** is a lightweight server monitoring and AI operations workflow designed for Linux hosts running Nginx or Apache.

It splits responsibilities into two planes:
- **Server Agent**: Python collector that tails logs and samples host metrics via `psutil`
- **AI Analyzer**: OpenClaw-side aggregator that explains failures, answers questions, and sends alerts

### ✨ Key Features

- 📊 **Real-Time Metrics**: CPU, memory, disk, load, network I/O via `psutil`
- 📝 **Log Parsing**: Nginx/Apache access and error log normalization
- 📈 **Traffic Analysis**: PV, UV, IP counts, QPS, bandwidth, status breakdown
- 🕷️ **Spider Detection**: Crawler family identification and traffic separation
- ⚠️ **Smart Alerts**: Threshold-based webhooks (DingTalk, WeCom, ServerChan)
- 🤖 **AI Diagnosis**: Natural-language error explanations and remediation guidance
- 📄 **Auto Reports**: Daily/Weekly/Monthly PDF reports with AI commentary
- 🔒 **Guarded Automation**: Optional auto-ban and auto-heal with cooldowns and audit logs

### 🎯 Use Cases

- Monitor Linux servers without replacing existing stack
- Get AI-powered error explanations instead of raw log dumps
- Automated daily/weekly ops reports with traffic trends and security insights
- Detect suspicious IPs, 404 scan bursts, and 5xx error spikes
- Safe auto-remediation with allowlists, TTLs, and audit trails

---

## 🆕 What's New in v1.1.2

### Multi-Site Monitoring

- **Matrix Configuration**: Monitor multiple domains on the same host with `sites[]` array
- **System Metrics**: Dedicated `system_metrics` section for host-global resources (CPU, memory, disk, network)
- **Scope Separation**: Host-global metrics separated from site-local traffic rollups via `__host__` scope

### Hardened Log Reading

- **Logrotate Support**: Handles inode changes, file truncation, and temporary file absence
- **Incremental Reading**: Robust state tracking across log rotations and restarts

### Guarded Automation

- **Dry-Run Mode**: Test automation policies before enabling real actions
- **Whitelist-Aware Auto-Ban**: Protects trusted IPs and known spiders (Googlebot, Bingbot, Baiduspider)
- **TTL-Based Unban**: Automatic unban after configurable TTL (default: 24 hours)
- **Cooldown Protection**: Prevents action storms with per-rule cooldowns
- **Mandatory Notifications**: All automation actions logged and notified

### SQLite Audit Tracking

- **`automation_actions` Table**: Complete audit trail of all automation events
- **`banned_ips` Table**: Track active bans with TTL and metadata

### Configuration

- **`config.example.yaml`**: Recommended starting point for v1.1.2 with multi-site, system_metrics, and Guarded Automation pre-configured

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/tankeito/server-mate.git
cd server-mate

# Install dependencies
python3 -m pip install psutil pyyaml matplotlib

# Optional: GeoIP enrichment
python3 -m pip install geoip2
```

### 2. Configuration

Generate or edit `config.yaml`:

For `1.1.2`, it is recommended to copy [`config.example.yaml`](config.example.yaml) to `config.yaml` first. In OpenClaw, keep `config.yaml`, `metrics.db`, `logs/`, and `reports/` inside the current workspace (`./`).

```yaml
agent:
  host_id: web-01
  site: example.com
  timezone: Asia/Shanghai
  mode: once

logs:
  access_log: ./logs/access.log
  error_log: ./logs/error.log

storage:
  database_file: ./metrics.db
  rollup_minutes: [10, 60]

notifications:
  webhooks:
    dingtalk:
      enabled: true
      url: https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN
  reports:
    report_language: zh
    report_export_dir: ./reports
    public_base_url: https://ops.example.com/reports
    daily:
      enabled: true
      push_time: "08:30"
      channels: [dingtalk]
```

### 3. Run Agent (Manual Test)

```bash
# One-shot collection
python3 scripts/server_agent.py --config config.yaml --once

# View collected metrics
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

# Monthly PDF report on 1st at 01:20
20 1 1 * * /usr/bin/env bash -lc 'python3 ./scripts/report_generator.py --config ./config.yaml pdf --range monthly --send >> ./logs/server-mate-report.log 2>&1'
```

---

## 📋 Architecture

### Two-Plane Design

```
┌─────────────────────────────────────────────────────────────┐
│  Server Agent (CentOS Host)                                 │
│  - psutil metrics (CPU, memory, disk, network)              │
│  - Log tailer (Nginx/Apache access + error)                 │
│  - JSON event emitter                                       │
│  - SQLite rollup writer                                     │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ SQLite / JSON events
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  AI Analyzer (OpenClaw)                                     │
│  - Aggregation & storage                                    │
│  - Natural-language query handler                           │
│  - AI error diagnosis                                       │
│  - Webhook alerts (DingTalk, WeCom, ServerChan)             │
│  - Guarded auto-ban / auto-heal                             │
│  - PDF report generator (Daily/Weekly/Monthly)              │
└─────────────────────────────────────────────────────────────┘
```

### Component Flow

1. **Agent Collection** → `system_snapshot`, `access_event`, `error_event`
2. **SQLite Rollups** → 10-minute and hourly buckets
3. **Report Generator** → Reads rollups, generates PDF/Markdown
4. **Webhook Center** → Sends alerts and reports
5. **AI Analysis** → Optional LLM-powered error explanations

---

## 📊 Data Contracts

### Core Event Types

| Event Type | Purpose | Key Fields |
|------------|---------|------------|
| `system_snapshot` | Host health metrics | `cpu_pct`, `memory_pct`, `disk_free_bytes`, `load_1m` |
| `access_event` | Parsed access log | `client_ip`, `uri`, `status`, `response_ms`, `user_agent` |
| `error_event` | Parsed error log | `severity`, `component`, `category`, `fingerprint`, `message` |
| `action_event` | Audit trail | `action`, `target`, `reason`, `dry_run`, `result`, `ttl_seconds` |

### Metric Definitions

| Metric | Definition |
|--------|-----------|
| **PV** | Total request count in selected window |
| **UV** | Unique visitor key (IP + user-agent fallback) |
| **IP Count** | Unique client IPs |
| **QPS** | `request_count / window_seconds` |
| **Slow Request** | `response_ms > threshold` (default: 2000ms) |
| **Bandwidth Out** | Sum of response bytes |

---

## ⚙️ Configuration Reference

### `agent` Section

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `host_id` | string | - | Logical host name for alerts/reports |
| `site` | string | - | Site identifier for rollups |
| `timezone` | string | `UTC` | Local timezone for bucket scheduling |
| `mode` | string | `once` | `once` or `daemon` |
| `poll_interval_seconds` | int | `60` | Agent loop interval (daemon mode) |

### `logs` Section

| Field | Type | Description |
|-------|------|-------------|
| `access_log` | string | Nginx/Apache access log path |
| `error_log` | string | Nginx/Apache error log path |

### `storage` Section

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `database_file` | string | `./server_agent.sqlite3` | SQLite database path |
| `rollup_minutes` | array | `[10, 60]` | Bucket granularities |

### `notifications.webhooks` Section

| Channel | Fields |
|---------|--------|
| `dingtalk` | `enabled`, `url`, `timeout_seconds`, `at_all` |
| `wecom` | `enabled`, `url`, `timeout_seconds` |
| `serverchan` | `enabled`, `sckey`, `timeout_seconds` |

### `notifications.reports` Section

| Field | Type | Description |
|-------|------|-------------|
| `report_language` | string | `zh` or `en` |
| `report_export_dir` | string | Externally exposed directory for PDFs |
| `public_base_url` | string | URL prefix for download links |
| `daily.enabled` | boolean | Enable daily reports |
| `daily.push_time` | string | `"08:30"` format |
| `weekly.push_weekday` | int | `1-7` (1 = Monday) |
| `monthly.push_day` | int | `1-28` |

---

## 📄 Report Types

### Daily Report

**Generated**: Every day at configured `push_time`

**Contents**:
- 📊 PV, UV, IP totals for prior 24 hours
- 🔥 Top pages, IPs, referers
- 🕷️ Spider traffic breakdown
- 📈 Status code distribution (2xx/3xx/4xx/5xx)
- ⚠️ Top errors and slow endpoints
- 🤖 AI health commentary (if enabled)

### Weekly Report

**Generated**: Every Monday at configured time

**Contents**:
- 📈 7-day traffic trend
- 🚫 Blocked IP trends
- 🕷️ Crawler traffic patterns
- ⚠️ Suspicious route clusters
- 🔄 Recurring error fingerprints
- 🤖 AI weekly summary

### Monthly Report

**Generated**: 1st of each month

**Contents**:
- 📊 30-day traffic and performance trend
- 💾 Disk growth analysis
- 📈 Bandwidth peak detection
- ⚠️ Capacity warnings
- 🔧 Remediation summary
- 🤖 AI monthly review

---

## 🚨 Alert Thresholds

| Alert Type | Default Threshold | Window |
|------------|------------------|--------|
| CPU High | `> 85%` | 5 consecutive minutes |
| Memory High | `> 85%` | 5 consecutive minutes |
| Disk Low | `< 10%` free | Instant |
| 5xx Burst | `> 20` errors | 1 minute |
| Suspicious IP | `> 200` RPM | 1 minute |
| 404 Scan Burst | Sudden spike | Short window |
| Slow Routes | `> 2000ms` avg | Alert window |

---

## 🔒 Safety & Automation

### Auto-Ban Policy (Opt-In)

**Requirements**:
- ✅ Allowlist support for trusted IPs
- ✅ Evidence of abuse (not flash crowd)
- ✅ Cooldown and per-hour action cap
- ✅ TTL (e.g., 24 hours)
- ✅ Audit record with exact command

**Good Candidates**:
- Repeated request-rate breaches from one IP
- Scanner-like user-agents + 404 spray patterns
- Brute-force hits against admin routes

### Auto-Heal Policy (Conservative)

**Requirements**:
- ✅ Repeated `502` or upstream-failure evidence
- ✅ Failing health check or secondary signal
- ✅ One restart attempt per cooldown window
- ✅ Post-action verification
- ✅ Escalation path when restart fails

**Preferred Sequence**:
1. Alert
2. Dry-run recommendation
3. One guarded restart of proven failing service
4. Re-check error rate and health
5. Escalate instead of looping

---

## 📁 Project Structure

```
server-mate/
├── SKILL.md                          # Skill definition and triggers
├── README.md                         # English documentation
├── README_ZH.md                      # Chinese documentation
├── user-guide.md                     # Detailed deployment guide
├── agents/
│   └── openai.yaml                  # OpenAI agent interface config
├── references/
│   ├── architecture.md              # System design and component boundaries
│   ├── data-contracts.md            # Event schemas and metric definitions
│   ├── ops-playbook.md              # Thresholds, alerts, and automation policies
│   └── sqlite-schema.md             # Database schema and query patterns
├── scripts/
│   ├── server_agent.py              # Main collector daemon
│   ├── report_generator.py          # PDF/Markdown report generator
│   └── webhook_center.py            # Webhook delivery service
└── config.yaml                       # Configuration file (generated)
```

---

## 🔍 Troubleshooting

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

### Webhook Message Contains Only Local Path

**Solution**:
1. Set `report_export_dir` in config
2. Set `public_base_url` in config
3. Expose export directory via Nginx or Apache

### No Report Data Appears

**Solution**:
1. Verify `database_file` path
2. Confirm agent is writing rollups
3. Check `site` and `host_id` match stored data

### Slow Routes or Abnormal IP Sections Are Empty

**Solution**:
- Ensure latest agent version has created `slow_request_rollups` and `suspicious_ip_rollups` tables

---

## 📞 Support

- **GitHub Issues**: https://github.com/tankeito/server-mate/issues
- **Repository**: https://github.com/tankeito/server-mate
- **Email**: tqd354@gmail.com

---

**Server-Mate** | Lightweight Server Monitoring & AI Ops

**Developed by tankeito** | MIT License | 2026
