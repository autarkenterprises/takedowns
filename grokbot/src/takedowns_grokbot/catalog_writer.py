"""
Append-only writer for README.md tables and instances.txt list entries.

Regression rule: every write must leave the previous file contents as an
exact UTF-8 prefix of the new contents. Historical rows are never rewritten.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from takedowns_grokbot.models import CandidateDraft
from takedowns_grokbot.queue_store import format_instances_entry

_ENTRY_NUM = re.compile(r"^(\d+)\.\s+", re.MULTILINE)
_TABLE_NUM = re.compile(r"^\|\s*(\d+)\s*\|", re.MULTILINE)


@dataclass
class AppendResult:
    """Outcome of a catalog append attempt."""

    added: int
    first_number: int
    last_number: int


def next_entry_number(instances_path: Path, readme_path: Path | None = None) -> int:
    """Return the next 1-based catalog number from existing files."""
    highest = 0
    if instances_path.exists():
        text = instances_path.read_text(encoding="utf-8")
        for m in _ENTRY_NUM.finditer(text):
            highest = max(highest, int(m.group(1)))
    if readme_path and readme_path.exists():
        text = readme_path.read_text(encoding="utf-8")
        for m in _TABLE_NUM.finditer(text):
            highest = max(highest, int(m.group(1)))
    return highest + 1


def _source_markdown(draft: CandidateDraft) -> str:
    """Build README citation chips: [label](url) ([archive](arch))."""
    parts: list[str] = []
    for i, src in enumerate(draft.sources):
        arch = draft.archive_urls.get(src)
        if not arch:
            raise ValueError(f"missing archive for source: {src}")
        label = "Source" if len(draft.sources) == 1 else f"Source {i + 1}"
        # Prefer a short host-based label when possible.
        host = re.sub(r"^www\.", "", re.sub(r"^https?://", "", src)).split("/")[0]
        if host:
            label = host
        parts.append(f"[{label}]({src}) ([archive]({arch}))")
    return " · ".join(parts)


def _readme_row(number: int, draft: CandidateDraft) -> str:
    who = draft.who.replace("|", "/")
    audience = draft.audience.replace("|", "/")
    when = draft.when.replace("|", "/")
    platform = draft.platform.replace("|", "/")
    what = draft.what_happened.replace("|", "/").replace("\n", " ")
    cites = _source_markdown(draft)
    return (
        f"| {number} | **{who}** | {audience} | {when} | {platform} | "
        f"{what} {cites} |"
    )


def _append_with_prefix_guard(path: Path, suffix: str) -> None:
    """
    Write path' = previous + suffix, asserting previous remains an exact prefix.
    """
    previous = path.read_text(encoding="utf-8") if path.exists() else ""
    # Ensure we separate sections cleanly.
    if previous and not previous.endswith("\n"):
        previous = previous + "\n"
    updated = previous + suffix
    if not updated.startswith(previous):
        raise RuntimeError(f"refusing write that would regress prefix: {path}")
    path.write_text(updated, encoding="utf-8")
    # Re-read verification (belt and suspenders against encode surprises).
    written = path.read_text(encoding="utf-8")
    if not written.startswith(previous):
        # Attempt restore.
        path.write_text(previous, encoding="utf-8")
        raise RuntimeError(f"prefix regression detected after write; restored {path}")


def append_candidates(
    readme_path: Path,
    instances_path: Path,
    drafts: list[CandidateDraft],
    batch_date: date | None = None,
) -> AppendResult:
    """
    Append one or more validated+archived drafts to both catalog surfaces.

    Empty input is a no-op. Each draft must already carry archive_urls for
    every sources[] entry.
    """
    if not drafts:
        return AppendResult(added=0, first_number=0, last_number=0)

    for draft in drafts:
        for src in draft.sources:
            if src not in draft.archive_urls or not draft.archive_urls[src]:
                raise ValueError(f"missing archive for source before append: {src}")

    start = next_entry_number(instances_path, readme_path)
    day = batch_date or date.today()

    instance_blocks: list[str] = [
        f"\n## Cloud Agent findings ({day.isoformat()})\n"
        "Auto-appended after validator + Wayback gates. Numbers continue the catalog.\n"
    ]
    table_lines = [
        f"\n## Cloud Agent findings ({day.isoformat()})\n",
        "\nValidated discoveries appended by the Cursor Cloud Agent "
        "(same inclusion bar; prior batches unchanged).\n",
        "\n| # | Who | Audience | When | Platform | What happened |\n",
        "|---|-----|----------|------|----------|---------------|\n",
    ]

    for offset, draft in enumerate(drafts):
        number = start + offset
        instance_blocks.append(format_instances_entry(draft, number))
        if not instance_blocks[-1].endswith("\n"):
            instance_blocks[-1] += "\n"
        table_lines.append(_readme_row(number, draft) + "\n")

    _append_with_prefix_guard(instances_path, "".join(instance_blocks))
    _append_with_prefix_guard(readme_path, "".join(table_lines))

    return AppendResult(
        added=len(drafts),
        first_number=start,
        last_number=start + len(drafts) - 1,
    )
