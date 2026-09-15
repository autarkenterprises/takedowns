"""
Parse instances.txt into a lightweight index for duplicate detection.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse, urlunparse


_ENTRY_START = re.compile(r"^(\d+)\.\s+(.+?)\s*$")
_URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)


def normalize_entity_name(name: str) -> str:
    """Lowercase, strip parenthetical aliases for fuzzy membership checks."""
    base = re.sub(r"\([^)]*\)", " ", name)
    base = re.sub(r"\s+", " ", base).strip().lower()
    return base


def normalize_source_url(url: str) -> str:
    """Normalize URLs enough to catch obvious duplicates (scheme/host/path)."""
    parsed = urlparse(url.strip())
    scheme = (parsed.scheme or "https").lower()
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/") or ""
    return urlunparse((scheme, netloc, path, "", "", ""))


@dataclass
class CatalogIndex:
    """In-memory view of who/what is already documented."""

    entity_names: set[str] = field(default_factory=set)
    source_urls: set[str] = field(default_factory=set)
    raw_headings: list[str] = field(default_factory=list)

    def contains_entity(self, name: str) -> bool:
        needle = normalize_entity_name(name)
        if not needle:
            return False
        if needle in self.entity_names:
            return True
        # Also match if the needle appears inside a known heading or vice versa.
        for known in self.entity_names:
            if needle in known or known in needle:
                return True
        return False

    def contains_source(self, url: str) -> bool:
        return normalize_source_url(url) in self.source_urls

    def summary_for_prompt(self, limit: int = 80) -> str:
        """Compact list of known entities for the Cloud Agent prompt."""
        names = sorted(self.raw_headings)[:limit]
        return "Known catalog entities (do not re-propose):\n- " + "\n- ".join(names)


def load_catalog_index(path: Path) -> CatalogIndex:
    """
    Parse the plaintext catalog.

    Entry headings look like ``1. Demolition Ranch (Matt Carriker)``.
    Source lines may be labeled ``Sources:`` / ``Source:`` or be indented URLs.
    """
    text = path.read_text(encoding="utf-8")
    index = CatalogIndex()
    for line in text.splitlines():
        m = _ENTRY_START.match(line.strip())
        if m:
            heading = m.group(2).strip()
            index.raw_headings.append(heading)
            index.entity_names.add(normalize_entity_name(heading))
            # Also index parenthetical names separately when present.
            for alias in re.findall(r"\(([^)]+)\)", heading):
                # Split "Greg/John Kinman" style aliases.
                for part in re.split(r"[/,]", alias):
                    part = part.strip()
                    if part:
                        index.entity_names.add(normalize_entity_name(part))
            continue
        for url in _URL_RE.findall(line):
            # Skip archive companion lines' wayback URLs for "known source" checks;
            # we care about original citations.
            if "web.archive.org" in url:
                continue
            index.source_urls.add(normalize_source_url(url))
    return index
