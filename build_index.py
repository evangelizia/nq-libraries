#!/usr/bin/env python3
"""Regenerates index.json from class/, bots/ and lua-bots/.

Deterministic on purpose: no timestamps, entries sorted by file name, so the
index only changes when the data changes and a diff means something.

    python3 build_index.py          # rewrite index.json
    python3 build_index.py --push   # rewrite, commit, push

Each entry carries the sha256 of its file, so a client can tell a stale cache
from a fresh one without downloading everything again. A Lua bot is a folder -
lua-bots/<id>/<id>.json beside <id>.lua - and its entry names both files, each
with its own digest. A preset with "publish": false builds but is not listed.
"""

import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
KINDS = ("class", "bots", "lua-bots")
SCHEMA = 1


def fail(message):
    print(f"index error: {message}", file=sys.stderr)
    sys.exit(1)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def entry(path):
    with path.open(encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError as exc:
            fail(f"{path.name}: {exc}")

    if not isinstance(data, dict):
        fail(f"{path.name}: must be an object")

    # A preset that is not published yet still builds, but no index row names
    # it, so a client cannot fetch what the author has not released.
    if data.get("publish") is False:
        return None

    pid = data.get("id")
    if not isinstance(pid, str) or not pid:
        fail(f"{path.name}: missing id")

    out = {"id": pid}
    for key in ("class", "role", "name"):
        if isinstance(data.get(key), str) and data[key]:
            out[key] = data[key]
    if isinstance(data.get("aliases"), list) and data["aliases"]:
        out["aliases"] = data["aliases"]

    out["file"] = path.relative_to(ROOT).as_posix()
    out["sha256"] = digest(path)
    return out


def body_of(manifest, pid):
    """The Lua body that sits beside its manifest in lua-bots/<id>/."""
    if manifest.parent.name != pid:
        fail(f"{manifest.name}: lua-bots needs the folder to be named for the id")
    body = manifest.with_suffix(".lua")
    if not body.is_file():
        fail(f"{manifest.name}: no {body.name} beside it")
    if body.stat().st_size == 0:
        fail(f"{body.name}: empty route")
    return body


def build():
    index = {"schema": SCHEMA}
    total = 0
    seen = {}

    for kind in KINDS:
        folder = ROOT / kind
        rows = []

        if folder.is_dir():
            glob = "*/*.json" if kind == "lua-bots" else "*.json"
            for path in sorted(folder.glob(glob)):
                row = entry(path)
                if row is None:
                    print(f"   {kind}: {path.name} is not published yet")
                    continue

                pid = row["id"]
                if pid in seen:
                    fail(f"duplicate id {pid!r} in {kind}/, also in {seen[pid]}")
                seen[pid] = f"{kind}/"

                if kind == "lua-bots":
                    body = body_of(path, pid)
                    row["lua"] = {
                        "file": body.relative_to(ROOT).as_posix(),
                        "sha256": digest(body),
                    }
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
