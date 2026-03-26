# Server-Mate User Guide

Version: `1.1.0`

## 1. What This Guide Covers

This guide is for operators who want to deploy `Server-Mate` on CentOS, Ubuntu, Debian, or other mainstream Linux servers.

It covers:

- Python and system dependencies
- multi-site `config.yaml` setup
- Daily / weekly / monthly report generation
- Guarded Automation safety rules and audit workflow
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
- Copy [`config.yaml.example`](/E:/ai/Server-Mate/config.yaml.example) to `config.yaml` and then adjust paths, webhooks, and automation switches for your environment.

If the file is missing, the agent can generate a default one automatically.

### 3.1 Full Example

```yaml
agent:
  host_id: web-01
  timezone: Asia/Shanghai
  mode: once
  state_file: ./server_agent_state.json

system_metrics:
  enabled: true
  disk_root: /
  collect_network_io: true

sites:
  - domain: agent.btc354.com
    site_host: agent.btc354.com
    access_log: /www/wwwlogs/agent.btc354.com.log
    error_log: /www/server/panel/vhost/nginx/agent.btc354.com.error.log
  - domain: api.example.com
    site_host: api.example.com
    access_log: /var/log/nginx/api.example.com.access.log
    error_log: /var/log/nginx/api.example.com.error.log

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
automation:
  dry_run: true
  auto_ban:
    enabled: false
    whitelist_ips: [127.0.0.1, "::1", 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16]
    whitelist_spiders: [googlebot, baiduspider, bingbot]
    ban_ttl_seconds: 86400
  auto_heal:
    enabled: false
    services: [php-fpm]
    cooldown_seconds: 3600
```

For a production-ready template, start from [`config.yaml.example`](/E:/ai/Server-Mate/config.yaml.example).

## 4. Parameter Reference

### 4.1 `agent`

- `host_id`
  - Logical host name shown in alerts and reports.
- `timezone`
  - Local timezone used for bucket closing, scheduling, and reports.
- `mode`
  - `once` or `daemon`.
- `poll_interval_seconds`
  - Agent loop interval in daemon mode.
- `state_file`
  - JSON cursor/state file for incremental log reads.

Legacy note:

- Older single-site keys such as `agent.site`, `agent.site_host`, and top-level `logs.*` are still normalized for compatibility, but new deployments should use `sites[]`.

### 4.2 `system_metrics`

- `enabled`
  - Whether host-global CPU, memory, disk, load, and network metrics are collected.
- `disk_root`
  - Filesystem mount point used by `psutil.disk_usage()`.
- `collect_network_io`
  - Whether to sample host-level RX or TX counters.

### 4.3 `sites`

Each item in `sites` is an independent business target:

- `domain`
  - Primary site identifier used in SQLite rollups, reports, and webhook notifications.
- `site_host`
  - Hostname used for referer/source classification.
- `enabled`
  - Whether this site participates in collection and report generation.
- `access_log`
  - Site-specific access log path.
- `error_log`
  - Site-specific error log path.

Important behavior:

- Server-Mate collects host metrics once per cycle, not once per site.
- Access and error logs are parsed independently for each configured site.
- `report_generator.py` will generate one report per site unless you pass `--site`.

### 4.4 `storage`

- `database_file`
  - SQLite database path.
- `rollup_minutes`
  - Bucket granularities to persist, for example `[10, 60]`.

### 4.5 `thresholds`

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

### 4.6 `notifications.webhooks`

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

### 4.7 `notifications.reports`

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

### 4.8 `notifications.reports.ai_analysis`

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

### 4.9 `automation`

Global switch:

- `dry_run`
  - Master safety switch for Guarded Automation.
  - When `true`, Server-Mate sends the automation notice and writes SQLite audit records, but never runs the real `iptables` or `systemctl` command.
  - Recommended default for first deployment: keep `dry_run: true` for several days.

`automation.auto_ban`:

- `enabled`
  - Enables auto-ban logic for suspicious IP bursts.
- `channels`
  - Webhook channels used for the automatic intervention notice.
- `whitelist_ips`
  - Absolute allowlist checked before any ban command.
- `whitelist_spiders`
  - Trusted crawler families that should never be auto-banned.
- `ban_ttl_seconds`
  - Ban lifetime before automatic release.
- `max_active_bans`
  - Hard cap to stop unbounded firewall growth.
- `command_template`
  - Shell template for the actual ban action.
- `unban_command_template`
  - Shell template used when TTL expires.

`automation.auto_heal`:

- `enabled`
  - Enables restart-based self-heal attempts.
- `services`
  - Service list that can be restarted.
- `trigger_kinds`
  - Alert kinds that are allowed to trigger self-heal.
- `cooldown_seconds`
  - Restart anti-flap lock. The same service is only allowed once per cooldown window.
- `command_template`
  - Shell template used for the restart command.

## 5. Multi-Site Configuration Guide

Use `sites[]` when one host serves multiple domains or applications.

Recommended pattern:

- Put only host-global settings in `agent`, `system_metrics`, `storage`, and shared webhook blocks.
- Put domain-specific log paths in `sites[]`.
- Keep `domain` stable over time because it becomes part of SQLite rollup keys and report filenames.

Example:

```yaml
sites:
  - domain: app.example.com
    access_log: /www/wwwlogs/app.example.com.log
    error_log: /www/server/panel/vhost/nginx/app.example.com.error.log
  - domain: api.example.com
    access_log: /var/log/nginx/api.example.com.access.log
    error_log: /var/log/nginx/api.example.com.error.log
```

Operational notes:

- One `server_agent.py --once` run will loop over every enabled site.
- One scheduled PDF generation run will emit one file per site automatically.
- For manual single-site inspection, use `--site`:

```bash
python3 scripts/report_generator.py --config config.yaml pdf --range daily --site agent.btc354.com --json
```

## 6. Guarded Automation Guide

### 6.1 Start in Dry-Run

Strong recommendation:

- Keep `automation.dry_run: true` during initial deployment.
- Watch the webhook notifications and SQLite audit tables for several days.
- Only switch to `false` after you trust the trigger thresholds, whitelist coverage, and operational blast radius.

With `dry_run: true`, Server-Mate will:

- evaluate the same auto-ban and auto-heal conditions
- send a high-priority automation notice to DingTalk, WeCom, or Feishu
- write audit rows into SQLite
- skip the real shell execution

### 6.2 Auto-Ban Rules

Auto-ban is designed for suspicious IP bursts such as CC-style request spikes.

Rules to follow:

- Treat `whitelist_ips` as mandatory, not optional.
- Keep loopback, RFC1918 private ranges, and trusted office VPN ranges in the whitelist.
- Keep trusted crawlers in `whitelist_spiders`.
- Do not disable the TTL release path unless an external controller such as fail2ban is managing expiry for you.
- Review `max_active_bans` before turning on production bans.

### 6.3 Auto-Heal Rules

Auto-heal is intentionally conservative.

Rules to follow:

- Only allow restartable services that your team is comfortable bouncing automatically.
- Keep `trigger_kinds` narrow. Start with `server_error_burst` only.
- Do not reduce `cooldown_seconds` aggressively. The default one-hour lock exists to prevent restart storms.
- If the same service continues failing after one restart window, prefer human intervention and incident escalation.

## 7. Generating Reports Manually

### 7.1 Daily Markdown

```bash
python3 scripts/report_generator.py --config config.yaml daily --date 2026-03-26 --json
```

### 7.2 Daily Markdown + Webhook Push

```bash
python3 scripts/report_generator.py --config config.yaml daily --date 2026-03-26 --send
```

### 7.3 Weekly PDF

```bash
python3 scripts/report_generator.py --config config.yaml pdf --range weekly --end-date 2026-03-26 --json
```

### 7.4 Monthly PDF + Webhook Push

```bash
python3 scripts/report_generator.py --config config.yaml pdf --range monthly --end-date 2026-03-31 --send
```

All three PDF modes now reuse the same final SaaS report layout:

- Daily: 24-hour traffic, hot pages / IPs / referers, spiders, status codes, visitor profile
- Weekly: 7-day trend using the same visual style, real SQLite aggregation, and AI commentary
- Monthly: 30-day trend using the same visual style, real SQLite aggregation, and AI commentary

## 8. Automated Scheduling Guide

This is the recommended production pattern:

- Run the collector in `--once` mode every 10 minutes.
- Run report generation as one-shot jobs.
- Let cron or systemd control timing instead of embedding a complex scheduler into the report process.

### 8.1 Open crontab

```bash
crontab -e
```

### 8.2 Data Capture Every 10 Minutes

This parses new access and error logs incrementally, refreshes in-memory state, and writes rollups into SQLite.

```cron
*/10 * * * * /usr/bin/python3 /opt/server-mate/scripts/server_agent.py --config /opt/server-mate/config.yaml --once >> /var/log/server-mate-agent.log 2>&1
```

### 8.3 Daily PDF Report at 01:00

This generates the previous day daily report and pushes it to the configured webhook channels.
In multi-site mode, this single cron entry will loop over every configured site and emit one report per domain.

```cron
0 1 * * * /usr/bin/python3 /opt/server-mate/scripts/report_generator.py --config /opt/server-mate/config.yaml pdf --range daily --send >> /var/log/server-mate-report.log 2>&1
```

### 8.4 Weekly PDF Report Every Monday at 01:10

```cron
10 1 * * 1 /usr/bin/python3 /opt/server-mate/scripts/report_generator.py --config /opt/server-mate/config.yaml pdf --range weekly --send >> /var/log/server-mate-report.log 2>&1
```

### 8.5 Monthly PDF Report on the 1st at 01:20

```cron
20 1 1 * * /usr/bin/python3 /opt/server-mate/scripts/report_generator.py --config /opt/server-mate/config.yaml pdf --range monthly --send >> /var/log/server-mate-report.log 2>&1
```

### 8.6 Optional Daily Markdown Instead of PDF

If you prefer a lighter daily push:

```cron
0 1 * * * /usr/bin/python3 /opt/server-mate/scripts/report_generator.py --config /opt/server-mate/config.yaml daily --send >> /var/log/server-mate-report.log 2>&1
```

### 8.7 Recommended Log Files

```bash
sudo touch /var/log/server-mate-agent.log /var/log/server-mate-report.log
sudo chmod 644 /var/log/server-mate-agent.log /var/log/server-mate-report.log
```

## 9. Scheduling with systemd

Recommended when you want stronger process control than cron.

### 9.1 Agent Service

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

### 9.2 Report Service + Timer Example

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

### 9.3 When to Use Cron vs systemd

- Use `cron` when you want the fastest deployment with simple one-line schedules.
- Use `systemd timers` when you want stronger observability, restart policy, and native service management.
- Use `server_agent.py --daemon` only when you explicitly want a resident process. For most production installs, `--once` plus cron is easier to audit and recover.

## 10. Exposing PDF Reports via Nginx

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

- `/srv/reports/server-mate/server-mate-example-com-weekly-2026-03-26-zh-cn.pdf`

becomes:

- `https://ops.example.com/reports/server-mate-example-com-weekly-2026-03-26-zh-cn.pdf`

Default naming pattern:

- `server-mate-{site}-{daily|weekly|monthly}-{YYYY-MM-DD}-{zh-cn|en}.pdf`

## 11. Exposing PDF Reports via Apache

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

## 12. Audit and Troubleshooting

### 12.1 Runtime Logs

Typical places to look first:

- `/var/log/server-mate-agent.log`
- `/var/log/server-mate-report.log`

These are especially useful when:

- a webhook endpoint is temporarily unreachable
- a log file was rotated and you want to confirm the collector recovered
- Guarded Automation sent a dry-run or failed-action notice

### 12.2 SQLite Audit Tables

Guarded Automation history is persisted in:

- `automation_actions`
  - Every dry-run, successful action, skipped cooldown action, unban, and failure.
- `banned_ips`
  - Ban lifetime tracking, expiry, and unban result.

Useful queries:

```bash
sqlite3 /opt/server-mate/server_agent.sqlite3 "SELECT created_at, site, action_type, target, status, dry_run, reason FROM automation_actions ORDER BY id DESC LIMIT 20;"
sqlite3 /opt/server-mate/server_agent.sqlite3 "SELECT site, ip_address, created_at, expires_at, lifted_at, lift_status FROM banned_ips ORDER BY id DESC LIMIT 20;"
```

### 12.3 Checklist

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
- If one site is missing from reports:
  - verify the site still exists in `sites[]`
  - confirm that the site's `enabled` flag is `true`
  - check both `access_log` and `error_log` paths for that domain
- If slow routes or abnormal IP sections are empty:
  - make sure the latest agent version has created `slow_request_rollups` and `suspicious_ip_rollups`
- If auto-ban or auto-heal did not run:
  - confirm `automation.dry_run` and `automation.auto_ban.enabled` or `automation.auto_heal.enabled`
  - query `automation_actions` to see whether the action was skipped by whitelist or cooldown
  - verify webhook notifications for `⚠️ 自动化干预通知`

## 13. Next Suggested Steps

- Enable AI diagnosis for complex `error_event` alerts
- Add GeoIP enrichment for country / region reports
- Add signed or expiring report download URLs if the report host is public
