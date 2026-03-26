# Server-Mate User Guide

## 1. What This Guide Covers

This guide is for operators who want to deploy `Server-Mate` on CentOS, Ubuntu, Debian, or other mainstream Linux servers.

It covers:

- Python and system dependencies
- `config.yaml` setup
- Daily / weekly / monthly report generation
- Cron and systemd scheduling
- Nginx or Apache download-link exposure for generated PDF reports

## 2. Prerequisites

### 2.1 Python Packages

Install the base runtime:

```bash
python3 -m pip install psutil
```

Install YAML support if you want native YAML parsing instead of JSON-compatible syntax:

```bash
python3 -m pip install pyyaml
```

Install report-generation packages:

```bash
python3 -m pip install matplotlib
```

Optional but recommended:

- `requests` is not required right now because webhook delivery uses the Python standard library.
- `sqlite3` is built into standard Python on most Linux distributions.
- Install `geoip2` if you want real province distribution in PDF reports:

```bash
python3 -m pip install geoip2
```

### 2.2 Linux Fonts for Chinese PDF Rendering

If `report_language: zh`, install at least one Chinese font package so matplotlib can render Chinese correctly.

Recommended packages:

- CentOS / Rocky / AlmaLinux:

```bash
sudo yum install google-noto-sans-cjk-ttc-fonts
```

- Ubuntu / Debian:

```bash
sudo apt-get update
sudo apt-get install fonts-noto-cjk
```

After installing fonts, refresh the font cache if needed:

```bash
fc-cache -fv
```

### 2.3 Log Paths

Server-Mate does not hardcode a single BT Panel layout. Always set log paths explicitly in `config.yaml`.

Common examples:

- BT Panel / Nginx:
  - `/www/wwwlogs/example.com.log`
  - `/www/server/panel/vhost/nginx/example.com.error.log`
- Ubuntu / Debian Nginx:
  - `/var/log/nginx/access.log`
  - `/var/log/nginx/error.log`
- Apache:
  - `/var/log/httpd/access_log`
  - `/var/log/httpd/error_log`
  - `/var/log/apache2/access.log`
  - `/var/log/apache2/error.log`

## 3. Configuration Overview

Main config file:

- `config.yaml`

If the file is missing, the agent can generate a default one automatically.

### 3.1 Minimal Example

```yaml
agent:
  host_id: web-01
  site: example.com
  timezone: Asia/Shanghai
  state_file: ./server_agent_state.json

logs:
  access_log: /var/log/nginx/access.log
  error_log: /var/log/nginx/error.log

storage:
  database_file: ./server_agent.sqlite3
  rollup_minutes: [10, 60]

notifications:
  webhooks:
    dingtalk:
      enabled: true
      url: https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN
  reports:
    report_language: zh
    report_export_dir: /srv/reports/server-mate
    public_base_url: https://ops.example.com/reports
    geoip_city_db: /opt/GeoLite2-City.mmdb
    ai_analysis:
      enabled: true
      simulate: false
      endpoint: https://api.openai.com/v1
      model: gpt-4o-mini
      api_key_env: OPENAI_API_KEY
      timeout_seconds: 20
    daily:
      enabled: true
      push_time: "08:30"
      output_dir: ./reports
      channels: [dingtalk]
    weekly:
      enabled: true
      push_weekday: 1
      push_time: "09:00"
      output_dir: ./reports
      channels: [dingtalk]
    monthly:
      enabled: true
      push_day: 1
      push_time: "09:30"
      output_dir: ./reports
      channels: [dingtalk]
```

## 4. Parameter Reference

### 4.1 `agent`

- `host_id`
  - Logical host name shown in alerts and reports.
- `site`
  - Site identifier used for rollups and filtering.
- `site_host`
  - Optional hostname used for referer/source classification.
- `timezone`
  - Local timezone used for bucket closing, scheduling, and reports.
- `disk_root`
  - Filesystem mount point used by `psutil.disk_usage()`.
- `mode`
  - `once` or `daemon`.
- `poll_interval_seconds`
  - Agent loop interval in daemon mode.
- `state_file`
  - JSON cursor/state file for incremental log reads.

### 4.2 `logs`

- `access_log`
  - Access log file path.
- `error_log`
  - Error log file path.

### 4.3 `storage`

- `database_file`
  - SQLite database path.
- `rollup_minutes`
  - Bucket granularities to persist, for example `[10, 60]`.

### 4.4 `thresholds`

Examples:

- `slow_ms`
  - Slow-request threshold in milliseconds.
- `attack_rpm_threshold`
  - Requests per minute threshold for suspicious IP detection.
- `cpu_pct`
  - CPU alert threshold.
- `memory_pct`
  - Memory alert threshold.
- `disk_free_ratio`
  - Disk free space threshold, for example `0.10`.

### 4.5 `notifications.webhooks`

Each channel supports:

- `enabled`
  - Whether the channel is active.
- `url`
  - Incoming webhook URL.
- `timeout_seconds`
  - HTTP timeout.

Additional DingTalk option:

- `at_all`
  - Whether the robot should mention everyone.

### 4.6 `notifications.reports`

Global report options:

- `report_language`
  - `zh` or `en`.
- `report_export_dir`
  - Optional externally exposed directory for copied PDF/Markdown files.
- `public_base_url`
  - Optional URL prefix used to build direct download links.
- `geoip_city_db`
  - Optional GeoIP City database path. When configured with `geoip2`, province-distribution charts use real IP geolocation. If omitted, Server-Mate falls back to `Unknown Region` / `未知地区`.

Per-schedule options:

- `output_dir`
  - Local report directory. This is always used first.
- `report_export_dir`
  - Optional override for the global export directory.
- `public_base_url`
  - Optional override for the global public URL.
- `channels`
  - Webhook channels used for report notifications.

Daily-specific:

- `push_time`
  - Example: `"08:30"`.
- `send_on_startup_if_missed`
  - Whether to backfill a missed report on process startup.

Weekly-specific:

- `push_weekday`
  - `1-7`, usually `1` for Monday.

Monthly-specific:

- `push_day`
  - `1-28`.

### 4.7 `notifications.reports.ai_analysis`

- `enabled`
  - Enables AI health commentary for daily / weekly / monthly PDF reports.
- `simulate`
  - When `true`, the generator uses a built-in fallback summary instead of calling a real LLM API.
- `endpoint`
  - Base OpenAI-compatible API endpoint. Example: `https://api.openai.com/v1`.
- `model`
  - Chat model name, for example `gpt-4o-mini`.
- `api_key_env`
  - Environment variable name that stores the API key. Default: `OPENAI_API_KEY`.
- `timeout_seconds`
  - HTTP timeout for the AI request.

Before generating reports with real AI analysis, export the API key:

```bash
export OPENAI_API_KEY="YOUR_REAL_API_KEY"
```

If you are using `systemd`, place the same variable in an Environment file or directly in the service unit.

## 5. Generating Reports Manually

### 5.1 Daily Markdown

```bash
python3 scripts/report_generator.py --config config.yaml daily --date 2026-03-26 --json
```

### 5.2 Daily Markdown + Webhook Push

```bash
python3 scripts/report_generator.py --config config.yaml daily --date 2026-03-26 --send
```

### 5.3 Weekly PDF

```bash
python3 scripts/report_generator.py --config config.yaml pdf --range weekly --end-date 2026-03-26 --json
```

### 5.4 Monthly PDF + Webhook Push

```bash
python3 scripts/report_generator.py --config config.yaml pdf --range monthly --end-date 2026-03-31 --send
```

All three PDF modes now reuse the same final SaaS report layout:

- Daily: 24-hour traffic, hot pages / IPs / referers, spiders, status codes, visitor profile
- Weekly: 7-day trend using the same visual style, real SQLite aggregation, and AI commentary
- Monthly: 30-day trend using the same visual style, real SQLite aggregation, and AI commentary

## 6. Automated Scheduling Guide

This is the recommended production pattern:

- Run the collector in `--once` mode every 10 minutes.
- Run report generation as one-shot jobs.
- Let cron or systemd control timing instead of embedding a complex scheduler into the report process.

### 6.1 Open crontab

```bash
crontab -e
```

### 6.2 Data Capture Every 10 Minutes

This parses new access and error logs incrementally, refreshes in-memory state, and writes rollups into SQLite.

```cron
*/10 * * * * /usr/bin/python3 /opt/server-mate/scripts/server_agent.py --config /opt/server-mate/config.yaml --once >> /var/log/server-mate-agent.log 2>&1
```

### 6.3 Daily PDF Report at 01:00

This generates the previous day daily report and pushes it to the configured webhook channels.

```cron
0 1 * * * /usr/bin/python3 /opt/server-mate/scripts/report_generator.py --config /opt/server-mate/config.yaml pdf --range daily --send >> /var/log/server-mate-report.log 2>&1
```

### 6.4 Weekly PDF Report Every Monday at 01:10

```cron
10 1 * * 1 /usr/bin/python3 /opt/server-mate/scripts/report_generator.py --config /opt/server-mate/config.yaml pdf --range weekly --send >> /var/log/server-mate-report.log 2>&1
```

### 6.5 Monthly PDF Report on the 1st at 01:20

```cron
20 1 1 * * /usr/bin/python3 /opt/server-mate/scripts/report_generator.py --config /opt/server-mate/config.yaml pdf --range monthly --send >> /var/log/server-mate-report.log 2>&1
```

### 6.6 Optional Daily Markdown Instead of PDF

If you prefer a lighter daily push:

```cron
0 1 * * * /usr/bin/python3 /opt/server-mate/scripts/report_generator.py --config /opt/server-mate/config.yaml daily --send >> /var/log/server-mate-report.log 2>&1
```

### 6.7 Recommended Log Files

```bash
sudo touch /var/log/server-mate-agent.log /var/log/server-mate-report.log
sudo chmod 644 /var/log/server-mate-agent.log /var/log/server-mate-report.log
```

## 7. Scheduling with systemd

Recommended when you want stronger process control than cron.

### 7.1 Agent Service

`/etc/systemd/system/server-mate-agent.service`

```ini
[Unit]
Description=Server-Mate Agent
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/server-mate
ExecStart=/usr/bin/python3 /opt/server-mate/scripts/server_agent.py --config /opt/server-mate/config.yaml --daemon
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 7.2 Report Service + Timer Example

`/etc/systemd/system/server-mate-weekly-report.service`

```ini
[Unit]
Description=Server-Mate Weekly PDF Report

[Service]
Type=oneshot
WorkingDirectory=/opt/server-mate
ExecStart=/usr/bin/python3 /opt/server-mate/scripts/report_generator.py --config /opt/server-mate/config.yaml pdf --range weekly --send
```

`/etc/systemd/system/server-mate-weekly-report.timer`

```ini
[Unit]
Description=Run Server-Mate Weekly PDF Report

[Timer]
OnCalendar=Mon *-*-* 09:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now server-mate-weekly-report.timer
```

### 7.3 When to Use Cron vs systemd

- Use `cron` when you want the fastest deployment with simple one-line schedules.
- Use `systemd timers` when you want stronger observability, restart policy, and native service management.
- Use `server_agent.py --daemon` only when you explicitly want a resident process. For most production installs, `--once` plus cron is easier to audit and recover.

## 8. Exposing PDF Reports via Nginx

Assume:

- `report_export_dir = /srv/reports/server-mate`
- `public_base_url = https://ops.example.com/reports`

Example Nginx config:

```nginx
server {
    listen 80;
    server_name ops.example.com;

    location /reports/ {
        alias /srv/reports/server-mate/;
        autoindex off;
        add_header Cache-Control "no-cache";
    }
}
```

After reloading Nginx, a generated file such as:

- `/srv/reports/server-mate/weekly_report_2026-03-26.pdf`

becomes:

- `https://ops.example.com/reports/weekly_report_2026-03-26.pdf`

## 9. Exposing PDF Reports via Apache

```apache
Alias /reports/ "/srv/reports/server-mate/"

<Directory "/srv/reports/server-mate/">
    Require all granted
    Options -Indexes
</Directory>
```

Reload Apache after changes:

```bash
sudo systemctl reload httpd
```

or:

```bash
sudo systemctl reload apache2
```

## 10. Troubleshooting Checklist

- If Chinese text shows as squares in PDFs:
  - install `fonts-noto-cjk` or an equivalent CJK font package
  - run `fc-cache -fv`
- If the webhook message contains only a local path:
  - set `report_export_dir`
  - set `public_base_url`
  - expose the export directory via Nginx or Apache
- If no report data appears:
  - verify `database_file`
  - confirm the agent is writing rollups
  - check `site` and `host_id` match the stored data
- If slow routes or abnormal IP sections are empty:
  - make sure the latest agent version has created `slow_request_rollups` and `suspicious_ip_rollups`

## 11. Next Suggested Steps

- Enable AI diagnosis for complex `error_event` alerts
- Add GeoIP enrichment for country / region reports
- Add signed or expiring report download URLs if the report host is public
