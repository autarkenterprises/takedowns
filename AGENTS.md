# Takedowns agent notes

This repository is the published catalog (`README.md`, `instances.txt`) plus
the GrokBot scanner (`grokbot/`).

## Cursor Cloud specific instructions

Daily discovery must run **on Cursor Cloud**, not a laptop process.

When this is a scheduled Cloud Agent / Automation run (or when asked to scan):

1. Confirm `XAI_API_KEY` is present in the environment (Cursor Dashboard → Cloud Agents → Secrets). If it is missing, stop and report; do not invent findings.
2. From the repo root:
   ```bash
   ./grokbot/scripts/run_scan.sh
   ```
3. The scanner appends only after validator + Wayback gates. Historical catalog bytes must remain an exact prefix of each file.
4. If `README.md` and/or `instances.txt` changed:
   - `git add README.md instances.txt`
   - Commit with a message like `Append GrokBot findings from YYYY-MM-DD scan.`
   - Checkout `master` if needed, fast-forward merge the scan commit, `git push` to the GitHub remote (`newrepo` / `origin`).
   - Do **not** open a GitHub pull request as the merge gate.
5. If the catalog is unchanged, make no commit.
6. Do not rewrite, re-rank, or edit existing numbered rows. Do not commit `.env`, `.venv`, or secrets.

Tests (optional sanity before commit):

```bash
cd grokbot && PYTHONPATH=src .venv/bin/python -m pytest -q
```

## Inclusion bar (unchanged)

Include ordinary lawful firearms content (reviews, sport photos, brand pages,
range demos). Exclude manufacturing tutorials, threats, and illegal sales.
Every published row needs http(s) citations with Wayback mirrors.
