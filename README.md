# nq-libraries

Bot routes and class presets for NeverQuest, served over raw GitHub. A client
refreshes `index.json`, compares each entry's `sha256` with the copy it already
holds, and downloads what changed.

- `bots/` — one JSON per route
- `lua-bots/<id>/` — a route whose body is Lua: the manifest in `<id>.json`
  beside the script in `<id>.lua`
- `class/` — one JSON per class preset
- `tools/gen.py` — builds a story route from a quest table, and the API reference
- `docs/bot-api.md` — every preset key, verb and condition, generated

## Publishing

```
python3 build_index.py          # rewrite index.json
python3 build_index.py --push   # rewrite, commit, push
```

The index is deterministic: entries sorted by file, each with the sha256 of the
file it names. A client only re-downloads what the digest says it is missing.
A Lua bot is two files with a digest each, so a fixed body does not re-download
the manifest and a fixed manifest does not re-download the body.

A manifest that says `"publish": false` is skipped: it still lives in the repo
for the client that bakes it, but no index row names it, so nothing downloads
an unfinished route.

## Lua bots

A Lua route is a whole bot in one script: loops, waits and the farm logic the
step format cannot express, run by the client's own Lua VM. It is still a preset
— the manifest keeps the id, name, notes, `combat`, `loot` and the guards — so
the folder holds both files and nothing else:

```
lua-bots/yokairep/yokairep.json   # manifest, no steps
lua-bots/yokairep/yokairep.lua    # the route
```

The index row carries the manifest and, under `lua`, the body:

```json
{"id": "yokairep", "file": "lua-bots/yokairep/yokairep.json", "sha256": "...",
 "lua": {"file": "lua-bots/yokairep/yokairep.lua", "sha256": "..."}}
```

The client lists them in **Bots** like any other preset and compiles the body
when it is loaded.

## Writing a route

A story is one line per quest. Put the table in `tools/routes/<id>.py` — the
file name is the id — and let the generator expand it:

```
python3 tools/gen.py            # bots/<id>.json from tools/routes/
python3 tools/gen.py --docs     # docs/bot-api.md
python3 tools/gen.py --check    # compare the catalog with the client's validator
```

`docs/bot-api.md` is the reference for the format: preset keys, step keys, every
verb and every condition, with the arguments each one takes.

A bot with no table in `tools/routes/` is hand-written and the generator leaves it
alone; `bots/<id>.json` for an id that does have one is an artifact.
