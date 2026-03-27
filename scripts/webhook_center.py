#!/usr/bin/env python3
"""Webhook delivery helpers for Server-Mate alerts and reports."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Iterable


SUPPORTED_CHANNELS = ("dingtalk", "wecom", "feishu")
SEVERITY_RANK = {"info": 0, "warning": 1, "critical": 2}


def normalize_channel_names(channels: Iterable[str] | None) -> list[str]:
    if not channels:
        return []
    normalized = []
    for channel in channels:
        name = str(channel or "").strip().lower()
        if name and name not in normalized:
            normalized.append(name)
    return normalized


def get_active_channels(
    config: dict[str, Any],
    channels: Iterable[str] | None = None,
) -> list[tuple[str, dict[str, Any]]]:
    notifications = config.get("notifications", {})
    webhooks = notifications.get("webhooks", {})
    requested = normalize_channel_names(channels) or list(SUPPORTED_CHANNELS)

    active = []
    for name in requested:
        channel_config = webhooks.get(name) or {}
        if not isinstance(channel_config, dict):
            continue
        if not channel_config.get("enabled"):
            continue
        if not str(channel_config.get("url") or "").strip():
            continue
        active.append((name, channel_config))
    return active


def markdown_to_feishu_post(title: str, markdown: str) -> dict[str, Any]:
    content = []
    for line in markdown.strip().splitlines():
        if not line.strip():
            continue
        content.append([{"tag": "text", "text": line}])
    if not content:
        content = [[{"tag": "text", "text": title}]]
    return {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": title,
                    "content": content,
                }
            }
        },
    }


def build_markdown_payload(
    channel: str,
    title: str,
    markdown: str,
    channel_config: dict[str, Any],
) -> dict[str, Any]:
    if channel == "dingtalk":
        return {
            "msgtype": "markdown",
            "markdown": {"title": title, "text": markdown},
            "at": {"isAtAll": bool(channel_config.get("at_all", False))},
        }
    if channel == "wecom":
        return {
            "msgtype": "markdown",
            "markdown": {"content": markdown},
        }
    if channel == "feishu":
        return markdown_to_feishu_post(title, markdown)
    raise ValueError(f"Unsupported webhook channel: {channel}")


def parse_response_body(raw_body: bytes) -> tuple[str, dict[str, Any] | None]:
    text = raw_body.decode("utf-8", errors="replace")
    try:
        return text, json.loads(text)
    except json.JSONDecodeError:
        return text, None


def response_is_success(
    channel: str,
    status_code: int,
    body_json: dict[str, Any] | None,
) -> bool:
    if status_code < 200 or status_code >= 300:
        return False
    if body_json is None:
        return False
    if channel == "dingtalk":
        return str(body_json.get("errcode")) == "0"
    if channel == "wecom":
        return str(body_json.get("errcode")) == "0"
    if channel == "feishu":
        return str(body_json.get("code")) == "0"
    return False


def post_json(
    url: str,
    payload: dict[str, Any],
    timeout_seconds: int = 10,
) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url=url,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw_body = response.read()
            body_text, body_json = parse_response_body(raw_body)
            return {
                "ok": True,
                "http_status": response.status,
                "body_text": body_text,
                "body_json": body_json,
            }
    except urllib.error.HTTPError as exc:
        raw_body = exc.read()
        body_text, body_json = parse_response_body(raw_body)
        return {
            "ok": False,
            "http_status": exc.code,
            "body_text": body_text,
            "body_json": body_json,
            "error": str(exc),
        }
    except urllib.error.URLError as exc:
        return {
            "ok": False,
            "http_status": None,
            "body_text": "",
            "body_json": None,
            "error": str(exc),
        }


def send_markdown_message(
    config: dict[str, Any],
    title: str,
    markdown: str,
    channels: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    results = []
    for channel, channel_config in get_active_channels(config, channels):
        payload = build_markdown_payload(channel, title, markdown, channel_config)
        timeout_seconds = max(int(channel_config.get("timeout_seconds", 10)), 1)
        response = post_json(channel_config["url"], payload, timeout_seconds)
        response["channel"] = channel
        response["success"] = response_is_success(
            channel,
            int(response["http_status"] or 0),
            response.get("body_json"),
        )
        results.append(response)
    return results

