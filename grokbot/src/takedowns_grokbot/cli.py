"""
CLI entrypoints for one-off scans without starting the web UI.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from takedowns_grokbot.grok_client import GrokClient
from takedowns_grokbot.scanner import run_scan

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run one GrokBot discovery scan and append validated findings."
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
    client = GrokClient()
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
