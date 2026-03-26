---
name: server-mate
description: Build or extend a lightweight server monitoring and AI operations workflow for CentOS hosts running Baota/BT Panel with Nginx or Apache. Use when Codex needs to collect psutil metrics, parse access or error logs, design JSON payloads or APIs, add webhook alerts, generate daily or weekly ops reports, answer natural-language monitoring questions, or implement guarded auto-ban and auto-heal behaviors.
---

# Server Mate

Use this skill to design or implement a two-plane monitoring system:
- a Python agent on the server that tails logs and samples host metrics
- an OpenClaw-side analyzer that aggregates data, explains failures, answers questions, and sends alerts

## Start

- Confirm the environment first: CentOS version, Baota/BT usage, Nginx or Apache, PHP-FPM layout, log paths, webhook target, and whether automated actions may touch a live host.
- Keep collection read-only until the user explicitly asks for automation. Add alerting before any auto-ban or auto-heal behavior.
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
- Prefer a generated `config.yaml` plus SQLite for local state and historical rollups before adding external services.
- Support configurable log paths. Do not hardcode one Baota site layout when the vhost config can be read instead.
- Emit structured JSON with timezone-aware timestamps, host or site identifiers, event type, and enough raw context to debug parser mistakes.
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
- Require cooldowns, max actions per window, and allowlists before running firewall or restart commands.
- Record an audit event for every alert, dry-run, ban, unban, restart, and failed remediation attempt.
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

Copyable cron examples:

```cron
*/10 * * * * /usr/bin/python3 /opt/server-mate/scripts/server_agent.py --config /opt/server-mate/config.yaml --once >> /var/log/server-mate-agent.log 2>&1
0 1 * * * /usr/bin/python3 /opt/server-mate/scripts/report_generator.py --config /opt/server-mate/config.yaml pdf --range daily --send >> /var/log/server-mate-report.log 2>&1
10 1 * * 1 /usr/bin/python3 /opt/server-mate/scripts/report_generator.py --config /opt/server-mate/config.yaml pdf --range weekly --send >> /var/log/server-mate-report.log 2>&1
20 1 1 * * /usr/bin/python3 /opt/server-mate/scripts/report_generator.py --config /opt/server-mate/config.yaml pdf --range monthly --send >> /var/log/server-mate-report.log 2>&1
```

Systemd note:

- If the host already standardizes on `systemd`, prefer `Type=oneshot` services plus timers for reports.
- Use `Restart=always` only for the long-running `--daemon` agent mode.

## Example requests

- "Design the ingestion API for Server-Mate."
- "Add 404 burst detection and webhook alerts."
- "Explain today's top 5xx error in plain language."
- "Plan a safe auto-heal flow for repeated 502 responses."
