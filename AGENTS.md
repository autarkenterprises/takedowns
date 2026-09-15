# Takedowns agent notes

This repository is the published catalog (`README.md`, `instances.txt`) plus
the ingest pipeline (`scan/`).

## Cursor Cloud specific instructions

You **are** the discovery engine. Use Cursor’s native Cloud Agent model and
built-in tools (web search / browse).

When this is a scheduled Cloud Agent / Automation run (or when asked to scan):

1. Read `README.md`, `instances.txt`, and this file. Do not re-propose entities
   already in the catalog.
2. Search the public web for **new** cases of platforms punishing firearms
   creators/brands for ordinary lawful content (reviews, sport photos, brand
   pages, range demos). Exclude manufacturing tutorials, threats, and illegal
   sales. Prefer recency × audience. Omit weak or uncitable cases.
3. Write `scan/data/inbox.json` as:
   ```json
   {
     "candidates": [
       {
         "who": "string",
         "audience": "string",
         "when": "string",
         "platform": "string",
         "what_happened": "string",
         "content_description": "string",
         "sources": ["https://..."],
         "fit_rationale": "string",
         "confidence": 0.0
       }
     ]
   }
   ```
   If nothing meets the bar, write `"candidates": []`. Never invent sources.
4. Run:
   ```bash
   ./scan/scripts/run_scan.sh scan/data/inbox.json
   ```
   The script validates, archives citations via Wayback, and appends to the
   catalog. Historical catalog bytes must remain an exact prefix of each file.
5. If `README.md` and/or `instances.txt` changed:
   - `git add README.md instances.txt`
   - Commit with a message like `Append Cloud Agent findings from YYYY-MM-DD scan.`
   - Fast-forward into `master` and `git push` to GitHub.
   - Do **not** open a GitHub pull request as the merge gate.
6. If the catalog is unchanged, make no commit. Do not commit `.env`, `.venv`,
   secrets, or `inbox.json` unless needed for audit (default: leave inbox
   untracked).
7. Do not rewrite, re-rank, or edit existing numbered rows.

Tests (optional sanity before commit):

```bash
cd scan && PYTHONPATH=src .venv/bin/python -m pytest -q
```

## Inclusion bar

Include ordinary lawful firearms content (reviews, sport photos, brand pages,
range demos). Exclude manufacturing tutorials, threats, and illegal sales.
Every published row needs http(s) citations with Wayback mirrors.
