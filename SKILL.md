---
name: server-mate
version: 1.2.0
description: Build or extend a lightweight server monitoring and AI operations workflow for Linux hosts running Nginx or Apache. Use when Codex needs to collect psutil metrics, parse access or error logs, design JSON payloads or APIs, add webhook alerts, generate daily or weekly ops reports, answer natural-language monitoring questions, or implement guarded auto-ban and auto-heal behaviors.
homepage: https://github.com/tankeito/server-mate
metadata:
  clawdbot:
    files:
      - scripts/*
      - references/*
      - config.example.yaml
      - user-guide.md
      - server-mate.service
      - _meta.json
---

# Server Mate

Version: `1.2.0`

Use this skill to design or implement a two-plane monitoring system:
- a Python agent on the server that tails logs and samples host metrics
- an OpenClaw-side analyzer that aggregates data, explains failures, answers questions, and sends alerts

## Start

- Confirm the environment first: Linux distribution, Nginx or Apache, PHP-FPM layout, log paths, webhook target, and whether automated actions may touch a live host.
- Keep collection read-only until the user explicitly asks for automation. Add alerting before any auto-ban or auto-heal behavior.
- In OpenClaw deployments, `OPENAI_API_KEY` is injected by the runtime when AI analysis is enabled. Do not ask the user to export it manually. Treat webhook URLs or tokens in `config.yaml` as secrets and do not commit them.
- Telegram delivery may read `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` when the config leaves those fields blank.
- Treat auto-ban and auto-heal as privileged features. They may execute operator-supplied firewall or service restart commands and should stay disabled or `dry_run: true` until reviewed.
- Use the references progressively instead of loading everything at once:
  - Read [references/architecture.md](references/architecture.md) for overall design, component boundaries, and rollout order.
  - Read [references/data-contracts.md](references/data-contracts.md) before defining JSON payloads, storage schemas, metrics, or natural-language query handlers.
  - Read [references/ops-playbook.md](references/ops-playbook.md) before implementing thresholds, webhooks, reports, auto-ban, or self-heal logic.
  - Read [references/sqlite-schema.md](references/sqlite-schema.md) before extending historical storage or report queries.
  - Use [scripts/server_agent.py](scripts/server_agent.py) as the collector, daemon entrypoint, and SQLite rollup writer.

## Delivery workflow

1. Map the request to one or more tracks.
   - Agent collection
   - Aggregation and storage
   - Alerting and reporting
   - AI diagnosis
   - Guarded remediation
2. Implement the smallest safe slice first.
   - Start with structured access, error, and system events.
   - Add rollup metrics and natural-language answers next.
   - Add webhook alerts after the counters are stable.
   - Enable auto-ban or auto-heal only when thresholds, cooldowns, allowlists, and audit logs already exist.
3. Validate with real or synthetic logs before changing production services.
4. Explain caveats in plain language.
   - Example: UV is often an approximation based on IP and user-agent unless the site provides a stronger visitor key.
   - Example: upload bandwidth is unavailable unless the access log includes request length or a similar field.

## Agent rules

- Prefer Python, `psutil`, and the standard library for the first implementation.
- Prefer a generated `./config.yaml` plus local SQLite state such as `./metrics.db` before adding external services.
- Keep generated artifacts inside the current skill workspace by default: `./config.yaml`, `./metrics.db`, `./logs/`, and `./reports/`. Do not default to `/opt`, `/var/log`, or other system-wide directories.
- Prefer the `system_metrics + sites[]` matrix layout from [config.example.yaml](config.example.yaml) instead of new single-site keys.
- Support configurable log paths. Do not hardcode site layouts when the vhost config can be read instead.
- Emit structured JSON with timezone-aware timestamps, host or site identifiers, event type, and enough raw context to debug parser mistakes.
- In multi-site mode, collect host CPU or memory metrics once per cycle and keep site log parsing isolated per domain.
- Separate parsing, aggregation, transport, and action execution so that HTTP push, stdout replay, file drop, or websocket transport can be swapped independently.
- Keep unknown lines and parser failures as first-class counters instead of dropping them silently.

## Analyzer rules

- Store raw events separately from derived counters.
- Model traffic, performance, security, spider, and error signals as independent reducers over the same event stream.
- Translate natural-language requests into:
  - a time window
  - filters
  - an aggregation
  - a presentation format
- For AI error explanations, pass the fingerprint, surrounding context, and normalized fields instead of dumping entire logs.

## Safety rules

- Treat auto-ban and auto-heal as opt-in features.
- Default Guarded Automation to `dry_run: true` and keep it there until the user has observed automation notifications and audit history for several days.
- Require cooldowns, max actions per window, and allowlists before running firewall or restart commands.
- Require whitelist checks before any ban command. Never ban loopback, RFC1918 private ranges, or trusted crawler families by default.
- Require TTL-based unban or an equivalent release plan for every ban. Do not create permanent firewall blocks from the first implementation.
- Record an audit event for every alert, dry-run, ban, unban, restart, and failed remediation attempt.
- Store audit history in SQLite tables such as `automation_actions` and `banned_ips`, and expose simple lookup queries in user-facing docs.
- Prefer one-shot remediation followed by escalation. Do not loop restarts.

## Report expectations

- Daily report: prior-day PV, UV, IP, request totals, bandwidth, status mix, top errors, and slow endpoints.
- Weekly report: blocked IP trends, crawler trends, suspicious route clusters, and recurring slow routes.
- Monthly report: bandwidth peak, disk growth, capacity warning, and remediation summary.

## Automation scheduling

Use external scheduling for production unless the user explicitly wants an always-on daemon-only design.

- Recommended ingestion pattern:
  - Run `server_agent.py --once` every 10 minutes from `cron` or a `systemd timer`.
  - This keeps log parsing incremental, writes SQLite rollups, and avoids duplicate resident processes.
- Recommended report pattern:
  - Run `report_generator.py` as one-shot scheduled jobs.
  - Daily PDF push at `01:00`.
  - Weekly PDF push every Monday at `01:10`.
  - Monthly PDF push on day `1` at `01:20`.
- In multi-site mode, a single scheduled `report_generator.py` run should iterate over every configured site unless the user explicitly passes `--site`.

## Release notes for 1.2.0

- Multi-site matrix config using `sites[]` plus global `system_metrics`
- Host-global metrics stored separately from site-local business rollups
- Logrotate-tolerant incremental readers with inode or truncate recovery
- Guarded Automation with `dry_run`, whitelist checks, TTL-based unban, cooldown-based auto-heal, and SQLite audit trail
- Telegram delivery with config-or-environment credential fallback
- Pre-send AI alert diagnosis with a compact two-sentence remediation block
- URL and referer truncation before dense PDF table rendering
- Bundled `server-mate.service` template for `systemd`-managed daemon startup

Copyable cron examples:

```cron
*/10 * * * * /usr/bin/env bash -lc 'python3 ./scripts/server_agent.py --config ./config.yaml --once >> ./logs/server-mate-agent.log 2>&1'
0 1 * * * /usr/bin/env bash -lc 'python3 ./scripts/report_generator.py --config ./config.yaml pdf --range daily --send >> ./logs/server-mate-report.log 2>&1'
10 1 * * 1 /usr/bin/env bash -lc 'python3 ./scripts/report_generator.py --config ./config.yaml pdf --range weekly --send >> ./logs/server-mate-report.log 2>&1'
20 1 1 * * /usr/bin/env bash -lc 'python3 ./scripts/report_generator.py --config ./config.yaml pdf --range monthly --send >> ./logs/server-mate-report.log 2>&1'
```

Systemd note:

- If the host already standardizes on `systemd`, prefer `Type=oneshot` services plus timers for reports.
- Use `Restart=always` only for the long-running `--daemon` agent mode.

## Example requests

- "Design the ingestion API for Server-Mate."
- "Add 404 burst detection and webhook alerts."
- "Explain today's top 5xx error in plain language."
- "Plan a safe auto-heal flow for repeated 502 responses."
