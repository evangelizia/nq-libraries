#!/usr/bin/env python3
"""Regenerates index.json from class/ and bots/.

Deterministic on purpose: no timestamps, entries sorted by file name, so the
index only changes when the data changes and a diff means something.

    python3 build_index.py          # rewrite index.json
    python3 build_index.py --push   # rewrite, commit, push

Each entry carries the sha256 of its file, so a client can tell a stale cache
from a fresh one without downloading everything again.
"""

import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
KINDS = ("class", "bots")
SCHEMA = 1


def fail(message):
    print(f"index error: {message}", file=sys.stderr)
    sys.exit(1)


def entry(path):
    with path.open(encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError as exc:
            fail(f"{path.name}: {exc}")

    if not isinstance(data, dict):
        fail(f"{path.name}: must be an object")

    pid = data.get("id")
    if not isinstance(pid, str) or not pid:
        fail(f"{path.name}: missing id")

    out = {"id": pid}
    for key in ("class", "role"):
        if isinstance(data.get(key), str) and data[key]:
            out[key] = data[key]
    if isinstance(data.get("aliases"), list) and data["aliases"]:
        out["aliases"] = data["aliases"]

    out["file"] = path.relative_to(ROOT).as_posix()
    out["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def build():
    index = {"schema": SCHEMA}
    total = 0

    for kind in KINDS:
        folder = ROOT / kind
        rows = []
        seen = set()

        if folder.is_dir():
            for path in sorted(folder.glob("*.json")):
                row = entry(path)
                if row["id"] in seen:
                    fail(f"duplicate id {row['id']!r} in {kind}/")
                seen.add(row["id"])
                rows.append(row)

        index[kind] = rows
        total += len(rows)
        print(f"   {kind}: {len(rows)}")

    (ROOT / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"index.json: {total} entr{'y' if total == 1 else 'ies'}")


def pull_push():
    if subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                      capture_output=True, text=True).stdout.strip() == "":
        print("nothing to commit")
        return

    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "index: rebuild"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)


if __name__ == "__main__":
    build()
    if "--push" in sys.argv[1:]:
        pull_push()
