"""
CLI: ingest Cursor Cloud Agent candidate JSON and append validated findings.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from takedowns_grokbot.scanner import StaticCandidateSource, run_scan

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Ingest candidate JSON from a Cursor Cloud Agent and append "
            "validated findings to the catalog. Does not call xAI/Grok."
        )
    )
    parser.add_argument(
        "--from-json",
        required=True,
        help="Path to {\"candidates\": [...]} written by the Cloud Agent",
    )
    parser.add_argument(
        "--catalog",
        default=os.environ.get("GROKBOT_CATALOG", str(ROOT.parent / "instances.txt")),
    )
    parser.add_argument(
        "--readme",
        default=os.environ.get("GROKBOT_README", str(ROOT.parent / "README.md")),
    )
    parser.add_argument(
        "--queue",
        default=os.environ.get("GROKBOT_QUEUE", str(ROOT / "data" / "candidates")),
    )
    parser.add_argument(
        "--runs",
        default=os.environ.get("GROKBOT_RUNS", str(ROOT / "data" / "runs")),
    )
    args = parser.parse_args(argv)
    json_path = Path(args.from_json)
    if not json_path.is_file():
        print(f"candidate JSON not found: {json_path}", file=sys.stderr)
        return 2
    client = StaticCandidateSource.from_json_file(json_path)
    report = run_scan(
        catalog_path=Path(args.catalog),
        readme_path=Path(args.readme),
        queue_dir=Path(args.queue),
        runs_dir=Path(args.runs),
        client=client,
    )
    print(json.dumps(report.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
