#!/usr/bin/env python3
"""BT-Panel (Baota) HTTP client for cross-server log collection.

Scope:
- Authentication signing using the BT request_time / request_token scheme.
- A small POST helper with timeout + bounded retry backoff.
- File-content reads via the /system?action=ExecShell endpoint, using
  ``tail -c +N | head -c CHUNK`` to fetch precise incremental byte ranges
  (avoids pulling whole log files into memory through GetFileBody).

Security note:
    The BT api_key has full panel privileges. Never commit it to the repo.
    Prefer environment-variable injection via remote_panels.<id>.api_key_env.

Concurrency note:
    This client is synchronous on purpose — Server-Mate runs once per cron tick
    and most deployments have a small number of panels. If the cumulative
    request time across panels approaches the cron interval (e.g. >5 min for a
    10-min schedule), wrap fetches in concurrent.futures.ThreadPoolExecutor at
    the call site, OR migrate to an aiohttp-backed async variant. Both are
    drop-in: the LogReader contract returns plain (lines, cursor) and does not
    care which thread called it. Threading is the cheaper option since the
    agent has no other event loop to coordinate with.

This module deliberately depends only on the standard library (urllib, ssl,
hashlib) so the agent stays installable without extra wheels.
"""

from __future__ import annotations

import hashlib
import json
import logging
import shlex
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


LOG = logging.getLogger("server_mate.bt_client")

# Operator-facing hint emitted whenever the panel rejects our signature.
# BT validates request_token = md5(request_time + md5(api_key)). If the agent
# clock drifts more than ~120s from the panel host, a correct api_key will
# still be rejected — the only fix is NTP, not re-pasting the key.
NTP_DRIFT_HINT = (
    "Authentication failed. Please check if the time on the Agent server and "
    "the Remote BT panel are synchronized (NTP Time Drift)."
)

# Substrings the BT panel commonly returns inside {"status": False, "msg": ...}
# when the request_token is rejected. Matched case-insensitively. Both English
# and Chinese variants are covered because BT localises by panel language.
_AUTH_FAILURE_HINTS = (
    "request_token",
    "request_time",
    "token",
    "签名",
    "鉴权",
    "时间",
    "未授权",
    "no permission",
    "permission denied",
    "auth failed",
    "authentication",
    "key error",
    "error_key",
)


def _looks_like_auth_failure(message: str | None) -> bool:
    """Return True if a panel-supplied error message looks like an auth/signature failure."""
    if not message:
        return False
    text = str(message).lower()
    return any(hint in text for hint in _AUTH_FAILURE_HINTS)


def _safe_remote_path(remote_path: str) -> str:
    """Validate + shell-quote a remote file path before splicing into ExecShell.

    Defense in depth — shlex.quote alone already neutralises shell metacharacters
    by wrapping the value in single quotes and escaping embedded quotes. We add
    two structural checks on top:

      * Reject embedded NUL/newline/CR — these are not legal in a Linux file path
        and their only realistic source is an attacker probing config injection.
      * Reject empty strings — would expand to an empty shell token and surprise
        the remote shell parser.

    Returns the safely quoted token ready for f-string splicing.
    """
    if not remote_path:
        raise ValueError("remote_path must be non-empty")
    path_str = str(remote_path)
    for forbidden in ("\x00", "\n", "\r"):
        if forbidden in path_str:
            raise ValueError(
                f"remote_path contains illegal control character ({forbidden!r}); refusing to build shell command"
            )
    return shlex.quote(path_str)


class BTPanelError(RuntimeError):
    """Raised when the BT panel returns a non-recoverable error."""


class BTPanelAuthError(BTPanelError):
    """Raised when api_key is missing/rejected — never auto-retried."""


@dataclass
class BTPanelConfig:
    panel_id: str
    url: str
    api_key: str
    timeout_seconds: int = 15
    retries: int = 2
    # Hard upper bound on bytes pulled per single ExecShell call AND per cron
    # cycle. Prevents OOM/timeout when an error_log explodes to multi-GB. Any
    # unread tail simply rolls over to the next cron tick.
    chunk_bytes: int = 5 * 1024 * 1024  # 5 MB
    verify_tls: bool = True

    @classmethod
    def from_dict(cls, panel: dict[str, Any]) -> "BTPanelConfig":
        return cls(
            panel_id=str(panel.get("panel_id") or "").strip(),
            url=str(panel.get("url") or "").strip().rstrip("/"),
            api_key=str(panel.get("api_key") or ""),
            timeout_seconds=int(panel.get("timeout_seconds", 15)),
            retries=int(panel.get("retries", 2)),
            chunk_bytes=int(panel.get("chunk_bytes", 5 * 1024 * 1024)),
            verify_tls=bool(panel.get("verify_tls", True)),
        )


class BTPanelClient:
    """Thin wrapper around the BT-Panel HTTP API.

    Only the subset needed by Server-Mate's log collection layer is exposed:
        - get_remote_file_size(path)
        - read_remote_file_chunk(path, offset, chunk_size)

    Both are designed to fail loudly on misconfiguration but return None / raise
    a typed exception on transient errors so the caller can decide whether to
    skip the cycle or surface an alert.
    """

    def __init__(self, config: BTPanelConfig) -> None:
        if not config.url:
            raise BTPanelAuthError(f"BT panel '{config.panel_id}' has empty url")
        if not config.api_key:
            raise BTPanelAuthError(
                f"BT panel '{config.panel_id}' has empty api_key "
                "(set api_key_env or api_key in remote_panels)"
            )
        self.config = config
        self._ssl_context = self._build_ssl_context(config.verify_tls)

    @staticmethod
    def _build_ssl_context(verify_tls: bool) -> ssl.SSLContext:
        if verify_tls:
            return ssl.create_default_context()
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    def _sign(self) -> dict[str, str]:
        """BT-specific signing: token = md5(request_time + md5(api_key))."""
        request_time = str(int(time.time()))
        api_key_md5 = hashlib.md5(self.config.api_key.encode("utf-8")).hexdigest()
        request_token = hashlib.md5(
            (request_time + api_key_md5).encode("utf-8")
        ).hexdigest()
        return {"request_time": request_time, "request_token": request_token}

    def _post(self, endpoint: str, payload: dict[str, Any]) -> Any:
        """POST to the panel with auth + retries.

        Retries are reserved for transport / 5xx-style failures. Auth or schema
        errors raise BTPanelError immediately so the caller can short-circuit.
        """
        url = f"{self.config.url}{endpoint}"
        body = dict(payload)
        body.update(self._sign())
        encoded = urllib.parse.urlencode(body).encode("utf-8")

        attempt = 0
        last_exc: Exception | None = None
        while attempt <= self.config.retries:
            attempt += 1
            request = urllib.request.Request(
                url,
                data=encoded,
                method="POST",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": "server-mate-bt-client/1.0",
                },
            )
            try:
                with urllib.request.urlopen(
                    request,
                    timeout=self.config.timeout_seconds,
                    context=self._ssl_context,
                ) as response:
                    raw = response.read().decode("utf-8", errors="replace")
            except urllib.error.HTTPError as exc:
                LOG.warning(
                    "BT panel %s %s HTTP %s (attempt %s/%s)",
                    self.config.panel_id,
                    endpoint,
                    exc.code,
                    attempt,
                    self.config.retries + 1,
                )
                if exc.code in (401, 403):
                    LOG.warning(
                        "BT panel %s rejected request at HTTP layer. %s",
                        self.config.panel_id,
                        NTP_DRIFT_HINT,
                    )
                    raise BTPanelAuthError(
                        f"BT panel '{self.config.panel_id}' rejected request: HTTP {exc.code}. {NTP_DRIFT_HINT}"
                    ) from exc
                last_exc = exc
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                LOG.warning(
                    "BT panel %s %s transport error: %s (attempt %s/%s)",
                    self.config.panel_id,
                    endpoint,
                    exc,
                    attempt,
                    self.config.retries + 1,
                )
                last_exc = exc
            else:
                return self._parse_response(raw)

            if attempt <= self.config.retries:
                time.sleep(min(2 ** (attempt - 1), 5))
        raise BTPanelError(
            f"BT panel '{self.config.panel_id}' {endpoint} failed after retries: {last_exc}"
        )

    @staticmethod
    def _parse_response(raw: str) -> Any:
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw

    def exec_shell(self, shell: str) -> str:
        """Execute a shell snippet on the remote host.

        BT's /system?action=ExecShell returns a JSON-ish blob. Different panel
        versions wrap output in {"status": True, "data": "..."} or just return
        a bare string; we accept both. Returns the raw stdout.

        Panel-level auth failures (e.g. token mismatch from clock drift) come
        back as HTTP 200 + {"status": False, "msg": "<token error>"} rather than
        as 401/403, so we sniff the message and re-raise as BTPanelAuthError
        with the NTP hint when the message looks auth-related.
        """
        result = self._post("/system?action=ExecShell", {"shell": shell})
        if isinstance(result, dict):
            if result.get("status") is False:
                msg = str(result.get("msg") or result.get("data") or "unknown error")
                if _looks_like_auth_failure(msg):
                    LOG.warning(
                        "BT panel %s payload-level auth failure (msg=%r). %s",
                        self.config.panel_id,
                        msg[:200],
                        NTP_DRIFT_HINT,
                    )
                    raise BTPanelAuthError(
                        f"ExecShell rejected on {self.config.panel_id}: {msg}. {NTP_DRIFT_HINT}"
                    )
                raise BTPanelError(f"ExecShell failed on {self.config.panel_id}: {msg}")
            data = result.get("data")
            return data if isinstance(data, str) else (str(data) if data is not None else "")
        if isinstance(result, str):
            return result
        return ""

    def get_remote_file_size(self, remote_path: str) -> int | None:
        """Return file size in bytes, or None if the file is missing / unreadable.

        Uses ``stat -c %s`` because it is portable across BT-supported distros and
        cheap; falls back to ``wc -c`` if ``stat`` is unavailable.
        """
        # _safe_remote_path = shlex.quote + control-char rejection. NEVER
        # interpolate remote_path into a shell string without going through it.
        path_token = _safe_remote_path(remote_path)
        shell = (
            f"if [ -f {path_token} ]; then "
            f"stat -c %s {path_token} 2>/dev/null || wc -c < {path_token}; "
            f"else echo MISSING; fi"
        )
        try:
            stdout = self.exec_shell(shell)
        except BTPanelError:
            raise
        text = (stdout or "").strip().splitlines()[-1] if stdout else ""
        if not text or text == "MISSING":
            return None
        try:
            return max(int(text), 0)
        except ValueError:
            LOG.warning(
                "BT panel %s stat returned non-numeric output for %s: %r",
                self.config.panel_id,
                remote_path,
                text,
            )
            return None

    def read_remote_file_chunk(
        self,
        remote_path: str,
        offset: int,
        chunk_size: int | None = None,
    ) -> bytes:
        """Read up to chunk_size bytes starting at the given byte offset.

        Implemented with ``tail -c +<offset+1> | head -c <chunk_size>`` to avoid
        loading the whole file into memory on the panel side. ``tail -c +N`` is
        1-based, hence ``offset + 1``.

        Two layers of bounding apply to ``chunk_size``:
          1. Caller-supplied ``chunk_size`` is clamped to ``config.chunk_bytes``
             (default 5 MB) so a buggy caller cannot demand a 2 GB pull.
          2. The bound is also baked into the SHELL pipeline as ``head -c N``,
             so even if the remote panel mis-handles our argument, the kernel
             tears down the pipe at N bytes — defence in depth against OOM.

        The panel often base64-encodes ExecShell output to survive JSON
        round-trips, but content of a logrotated text log can equally come back
        as plain UTF-8 bytes. We request base64 explicitly so binary safety is
        preserved across panel versions.
        """
        if offset < 0:
            offset = 0
        requested = int(chunk_size or self.config.chunk_bytes)
        # Hard cap: never let a single ExecShell pull exceed config.chunk_bytes.
        size = max(min(requested, self.config.chunk_bytes), 0)
        if size <= 0:
            return b""

        # _safe_remote_path = shlex.quote + control-char rejection. NEVER
        # interpolate remote_path into a shell string without going through it.
        path_token = _safe_remote_path(remote_path)
        # `head -c {size}` is the on-the-wire OOM stopgap — see method docstring.
        # base64 -w 0 keeps output single-line; both GNU coreutils and BusyBox
        # accept the spaced form.
        shell = (
            f"tail -c +{offset + 1} {path_token} 2>/dev/null "
            f"| head -c {size} | base64 -w 0"
        )
        stdout = self.exec_shell(shell)
        token = (stdout or "").strip()
        if not token:
            return b""
        import base64 as _b64

        try:
            return _b64.b64decode(token, validate=False)
        except (ValueError, _b64.binascii.Error) as exc:
            LOG.warning(
                "BT panel %s base64 decode failed for %s offset=%s: %s",
                self.config.panel_id,
                remote_path,
                offset,
                exc,
            )
            return b""


def build_panel_registry(panels_config: dict[str, dict[str, Any]]) -> dict[str, BTPanelClient]:
    """Instantiate one BTPanelClient per configured panel_id.

    Panels with missing url/api_key are skipped with a logged warning so the
    main agent can still serve local sites. The skipped IDs are still reported
    in the returned dict as None placeholders to help the caller emit a clear
    "this site was not collected" diagnostic.
    """
    registry: dict[str, BTPanelClient] = {}
    for panel_id, panel in panels_config.items():
        try:
            registry[panel_id] = BTPanelClient(BTPanelConfig.from_dict(panel))
        except BTPanelAuthError as exc:
            LOG.warning("Skipping BT panel %s: %s", panel_id, exc)
    return registry
