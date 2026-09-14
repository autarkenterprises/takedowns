"""
Wayback Machine helpers for citation durability (augment, never replace).
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable


UA = {"User-Agent": "takedowns-grokbot/0.1 (research catalog archiver)"}


def _fetch(url: str, timeout: int = 60) -> tuple[int, str, dict]:
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace"), dict(resp.headers)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, body, dict(exc.headers)


def find_existing_archive(url: str) -> str | None:
    """Return a Wayback URL for an existing snapshot, if any."""
    q = urllib.parse.urlencode(
        {
            "url": url,
            "output": "json",
            "fl": "timestamp,original,statuscode",
            "filter": "statuscode:200",
            "limit": "1",
            "fastLatest": "true",
        }
    )
    try:
        status, body, _ = _fetch(f"https://web.archive.org/cdx/search/cdx?{q}", timeout=45)
        if status == 200 and body.strip():
            data = json.loads(body)
            if len(data) > 1:
                ts, original = data[1][0], data[1][1]
                return f"https://web.archive.org/web/{ts}/{original}"
    except Exception:
        pass

    try:
        status, body, _ = _fetch(
            f"https://archive.org/wayback/available?url={urllib.parse.quote(url, safe='')}",
            timeout=45,
        )
        if status == 200:
            snap = json.loads(body).get("archived_snapshots", {}).get("closest")
            if snap and snap.get("available") and snap.get("url"):
                arch = snap["url"]
                if arch.startswith("http://"):
                    arch = "https://" + arch[len("http://") :]
                return arch
    except Exception:
        pass
    return None


def save_to_wayback(
    url: str,
    sleep: Callable[[float], None] = time.sleep,
    max_polls: int = 40,
) -> str | None:
    """
    Submit a URL to Wayback save and poll until a snapshot URL is available.
    """
    form = urllib.parse.urlencode({"url": url}).encode("utf-8")
    req = urllib.request.Request(
        "https://web.archive.org/save/",
        data=form,
        headers={**UA, "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")

    import re

    m = re.search(r'spn\.watchJob\("([^"]+)"', body) or re.search(
        r'"job_id"\s*:\s*"([^"]+)"', body
    )
    if not m:
        # Sometimes the archive link is inline.
        m2 = re.search(r"https://web\.archive\.org/web/\d{14}/[^\s\"'<>]+", body)
        return m2.group(0) if m2 else None

    job_id = m.group(1)
    for _ in range(max_polls):
        sleep(3)
        status, body, _ = _fetch(f"https://web.archive.org/save/status/{job_id}", timeout=60)
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            continue
        if data.get("status") == "success":
            ts = data.get("timestamp")
            original = data.get("original_url") or url
            return f"https://web.archive.org/web/{ts}/{original}"
        if data.get("status") in ("error", "failed"):
            return None
    return None


def ensure_archives(urls: list[str]) -> dict[str, str]:
    """Map each source URL to an archive.org mirror, saving when missing."""
    out: dict[str, str] = {}
    for url in urls:
        existing = find_existing_archive(url)
        if existing:
            out[url] = existing
            continue
        saved = save_to_wayback(url)
        if saved:
            out[url] = saved
    return out
