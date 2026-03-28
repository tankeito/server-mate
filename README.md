English | [荳ｭ譁Ⅹ(README_ZH.md)

---

# 箕・・Server-Mate | Lightweight Server Monitoring & AI Ops

> A two-plane monitoring system for Linux hosts running Nginx or Apache.

[![Version](https://img.shields.io/badge/version-1.3.1-blue.svg)]()
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-success.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-CentOS%2FUbuntu%2FDebian-lightgrey.svg)](https://linux.org)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Web Server](https://img.shields.io/badge/Web%20Server-Nginx%2FApache-orange.svg)](https://nginx.org)

---

## 当 Overview

**Server-Mate** is a lightweight server monitoring and AI operations workflow designed for Linux hosts running Nginx or Apache.

It splits responsibilities into two planes:
- **Server Agent**: Python collector that tails logs and samples host metrics via `psutil`
- **AI Analyzer**: OpenClaw-side aggregator that explains failures, answers questions, and sends alerts

### 笨ｨ Key Features

- 投 **Real-Time Metrics**: CPU, memory, disk, load, network I/O via `psutil`
- 統 **Log Parsing**: Nginx/Apache access and error log normalization
- 嶋 **Traffic Analysis**: PV, UV, IP counts, QPS, bandwidth, status breakdown
- 聞・・**Spider Detection**: Crawler family identification and traffic separation
- 笞・・**Smart Alerts**: Threshold-based webhooks (DingTalk, WeCom, Feishu, Telegram)
- 孱・・**SSH Security Shield**: auth log brute-force detection linked with Guarded Automation auto-ban
- ､・**AI Diagnosis**: Natural-language error explanations and remediation guidance
- 塘 **Auto Reports**: Daily/Weekly/Monthly PDF reports with AI commentary
- 白 **SSL Expiry Checks**: certificate remaining-days inspection in PDF headers and webhook summaries
- 白 **Guarded Automation**: Optional auto-ban and auto-heal with cooldowns and audit logs

### 識 Use Cases

- Monitor Linux servers without replacing existing stack
- Get AI-powered error explanations instead of raw log dumps
- Automated daily/weekly ops reports with traffic trends and security insights
- Detect suspicious IPs, 404 scan bursts, and 5xx error spikes
- Safe auto-remediation with allowlists, TTLs, and audit trails

---

## ・ What's New in v1.3.1

### SSH Security Shield

- **Auth Log Parsing**: incrementally parses `logs.auth_log` (or auto-detects `/var/log/auth.log` / `/var/log/secure`) for `Failed password` fingerprints
- **Linked Auto-Ban**: repeated SSH failures now raise `ssh_brute_force` alerts and can flow into the existing whitelist-aware auto-ban pipeline

### SSL Expiry Checker

- **Certificate Inspection**: report generation now checks each configured site certificate with Python `ssl` and `socket`
- **Visible Everywhere**: remaining days appear in PDF overview blocks and webhook markdown summaries, with warning markers below 15 days

### PDF Overflow Guard

- **URL / Referer Truncation**: query strings are removed before table rendering, then long text is hard-truncated
- **Stable Table Layouts**: oversized tokens no longer break dense PDF pages

### Telegram Push

- **New Channel**: webhook center now supports Telegram bot delivery
- **Env Fallback**: `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are used when config values are empty

### Out-of-the-box GeoIP

- **Auto-Provisioning**: The report generator now automatically downloads the required GeoLite2 `.mmdb` database from a public mirror if it's missing, delivering zero-config IP geolocation.
- **MaxMind-First Workflow**: if `./data/GeoIP.conf` exists and `geoipupdate` is installed, Server-Mate now refreshes GeoLite2 from your own MaxMind account before falling back to the public mirror.

### AI Alert Diagnosis

- **Pre-Send AI Review**: warning and critical alerts can call the shared AI endpoint before webhook delivery
- **Two-Sentence Output**: alert cards append a compact `庁 AI 譎ｺ閭ｽ隸頑妙` block with plain-language cause and next action

### systemd Template

- **`--generate-service`**: the agent can print a host-local systemd unit template for daemon hosting with `Restart=always`

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

- **`config.example.yaml`**: Recommended starting point for v1.3.1 with multi-site, Telegram, SSH auth monitoring, SSL checks, AI alert diagnosis, and Guarded Automation pre-configured

---

## 噫 Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/tankeito/server-mate.git
cd server-mate

# Install dependencies
python3 -m pip install psutil pyyaml matplotlib

# Optional: GeoIP enrichment
python3 -m pip install geoip2

# Optional: official MaxMind updater
# CentOS / Rocky / AlmaLinux: sudo yum install geoipupdate
# Ubuntu / Debian: sudo apt-get install geoipupdate
```

### 2. Configuration

Generate or edit `config.yaml`:

For `1.3.1`, it is recommended to copy [`config.example.yaml`](config.example.yaml) to `config.yaml` first. In OpenClaw, keep `config.yaml`, `metrics.db`, `logs/`, and `reports/` inside the current workspace (`./`).

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

logs:
  auth_log: ""

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
    daily:
      enabled: true
      push_time: "08:30"
      channels: [dingtalk]
```

### 2.1 GeoIP Notes

- Put your MaxMind config at `./data/GeoIP.conf`.
- Start from [`data/GeoIP.conf.example`](data/GeoIP.conf.example) and keep the real file out of Git.
- Free GeoLite2 account: [MaxMind GeoLite sign up](https://www.maxmind.com/en/geolite2/signup)
- License key guide: [Generate a License Key](https://support.maxmind.com/hc/en-us/articles/4407111582235-Generate-a-License-Key)
- `geoip_update_config` is optional, but `./data/GeoIP.conf` is the recommended local path.
- If you do not want to use MaxMind directly, Server-Mate still falls back to the public `.mmdb` mirror.
- If a MaxMind key was ever exposed in plain text, rotate it before production use.

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

## 搭 Architecture

### Two-Plane Design

```
笏娯楳笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏・
笏・ Server Agent (CentOS Host)                                 笏・
笏・ - psutil metrics (CPU, memory, disk, network)              笏・
笏・ - Log tailer (Nginx/Apache access + error)                 笏・
笏・ - JSON event emitter                                       笏・
笏・ - SQLite rollup writer                                     笏・
笏披楳笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏・
                          笏・
                          笏・SQLite / JSON events
                          笆ｼ
笏娯楳笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏・
笏・ AI Analyzer (OpenClaw)                                     笏・
笏・ - Aggregation & storage                                    笏・
笏・ - Natural-language query handler                           笏・
笏・ - AI error diagnosis                                       笏・
笏・ - Webhook alerts (DingTalk, WeCom, Feishu, Telegram)       笏・
笏・ - Guarded auto-ban / auto-heal                             笏・
笏・ - PDF report generator (Daily/Weekly/Monthly)              笏・
笏披楳笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏・
```

### Component Flow

1. **Agent Collection** 竊・`system_snapshot`, `access_event`, `error_event`
2. **SQLite Rollups** 竊・10-minute and hourly buckets
3. **Report Generator** 竊・Reads rollups, generates PDF/Markdown
4. **Webhook Center** 竊・Sends alerts and reports
5. **AI Analysis** 竊・Optional LLM-powered error explanations

---

## 投 Data Contracts

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

## 笞呻ｸ・Configuration Reference

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
| `database_file` | string | `./metrics.db` | SQLite database path |
| `rollup_minutes` | array | `[10, 60]` | Bucket granularities |

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
| `report_export_dir` | string | Externally exposed directory for PDFs |
| `public_base_url` | string | URL prefix for download links |
| `daily.enabled` | boolean | Enable daily reports |
| `daily.push_time` | string | `"08:30"` format |
| `weekly.push_weekday` | int | `1-7` (1 = Monday) |
| `monthly.push_day` | int | `1-28` |

---

## 塘 Report Types

### Daily Report

**Generated**: Every day at configured `push_time`

**Contents**:
- 投 PV, UV, IP totals for prior 24 hours
- 櫨 Top pages, IPs, referers
- 聞・・Spider traffic breakdown
- 嶋 Status code distribution (2xx/3xx/4xx/5xx)
- 笞・・Top errors and slow endpoints
- ､・AI health commentary (if enabled)

### Weekly Report

**Generated**: Every Monday at configured time

**Contents**:
- 嶋 7-day traffic trend
- 圻 Blocked IP trends
- 聞・・Crawler traffic patterns
- 笞・・Suspicious route clusters
- 売 Recurring error fingerprints
- ､・AI weekly summary

### Monthly Report

**Generated**: 1st of each month

**Contents**:
- 投 30-day traffic and performance trend
- 沈 Disk growth analysis
- 嶋 Bandwidth peak detection
- 笞・・Capacity warnings
- 肌 Remediation summary
- ､・AI monthly review

---

## 圷 Alert Thresholds

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

## 白 Safety & Automation

### Auto-Ban Policy (Opt-In)

**Requirements**:
- 笨・Allowlist support for trusted IPs
- 笨・Evidence of abuse (not flash crowd)
- 笨・Cooldown and per-hour action cap
- 笨・TTL (e.g., 24 hours)
- 笨・Audit record with exact command

**Good Candidates**:
- Repeated request-rate breaches from one IP
- Scanner-like user-agents + 404 spray patterns
- Brute-force hits against admin routes

### Auto-Heal Policy (Conservative)

**Requirements**:
- 笨・Repeated `502` or upstream-failure evidence
- 笨・Failing health check or secondary signal
- 笨・One restart attempt per cooldown window
- 笨・Post-action verification
- 笨・Escalation path when restart fails

**Preferred Sequence**:
1. Alert
2. Dry-run recommendation
3. One guarded restart of proven failing service
4. Re-check error rate and health
5. Escalate instead of looping

---

## 刀 Project Structure

```
server-mate/
笏懌楳笏 SKILL.md                          # Skill definition and triggers
笏懌楳笏 README.md                         # English documentation
笏懌楳笏 README_ZH.md                      # Chinese documentation
笏懌楳笏 user-guide.md                     # Detailed deployment guide
笏懌楳笏 config.example.yaml               # Full example config template
笏懌楳笏 data/
笏・  笏披楳笏 GeoIP.conf.example          # MaxMind GeoLite2 template (copy to ./data/GeoIP.conf)
笏懌楳笏 agents/
笏・  笏披楳笏 openai.yaml                  # OpenAI agent interface config
笏懌楳笏 references/
笏・  笏懌楳笏 architecture.md              # System design and component boundaries
笏・  笏懌楳笏 data-contracts.md            # Event schemas and metric definitions
笏・  笏懌楳笏 ops-playbook.md              # Thresholds, alerts, and automation policies
笏・  笏披楳笏 sqlite-schema.md             # Database schema and query patterns
笏懌楳笏 scripts/
笏・  笏懌楳笏 server_agent.py              # Main collector daemon
笏・  笏懌楳笏 report_generator.py          # PDF/Markdown report generator
笏・  笏披楳笏 webhook_center.py            # Webhook delivery service
笏披楳笏 config.yaml                       # Configuration file (generated)
```

---

## 剥 Troubleshooting

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

## 到 Support

- **GitHub Issues**: https://github.com/tankeito/server-mate/issues
- **Repository**: https://github.com/tankeito/server-mate
- **Email**: tqd354@gmail.com

---

**Server-Mate** | Lightweight Server Monitoring & AI Ops

**Developed by tankeito** | MIT License | 2026
