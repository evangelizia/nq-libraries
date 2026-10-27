#!/usr/bin/env python3
"""Builds bot presets from the tables in tools/routes/, and the API reference.

A story route is one line per quest plus a preset header; the repeating part -
accept, walk there, farm or click, turn in, come back - is generated. What comes
out is the same JSON the client downloads, in the same hand-written shape, so a
generated route and a written one are indistinguishable and either can be edited
later by hand.

    python3 tools/gen.py             # bots/<id>.json from tools/routes/
    python3 tools/gen.py --docs      # docs/bot-api.md
    python3 tools/gen.py --check     # confirm the catalog against the client's
                                     # own validator, when this repo sits inside
                                     # a client checkout

A route file holds two names: PRESET (everything in the preset except the steps)
and QUESTS (one Quest per quest, in the order the story runs them).
"""

import importlib.util
import json
import pathlib
import sys
from typing import NamedTuple

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
ROUTES = TOOLS / "routes"
BOTS = ROOT / "bots"
DOCS = ROOT / "docs"

FIGHT, MAP, MULTI = "fight", "map", "multi"
KINDS = (FIGHT, MAP, MULTI)

GAP = object()


class Quest(NamedTuple):
    """One quest of a chain: where it happens and what the step does there.

    `items` are map item ids, sent in order; `blank` moves the character to the
    Blank cell first, where nothing can reach it, which is what a click wants
    when the cell it belongs to has mobs in it. Left as None, a click does that
    and a fight does not.
    """

    id: int
    kind: str
    map: str
    cell: str = "Enter"
    pad: str = "Spawn"
    items: tuple = ()
    blank: bool = None

    def moves_to_blank(self):
        return (self.kind in (MAP, MULTI)) if self.blank is None else self.blank


class Reward(NamedTuple):
    """A shop item that marks the route as finished, bought at the end."""

    map: str
    shop: int
    item: str


# ------------------------------------------------------------------- catalog

PRESET_KEYS = [
    ("schema", 1, "always 1"),
    ("id", "string", "unique id, also the file name"),
    ("name", "string", "what the Bots tab shows"),
    ("bundle", "bool", "false keeps the preset out of the apk; the library ships it"),
    ("once", "bool", "the route runs its quests one time, remembering what it handed in"),
    ("notes", "string", "what the route does and why, for whoever reads it next"),
    ("pickup", "bool", "claim every non-temp drop, not only the listed ones"),
    ("loot", "list", "item names to claim; unlisted rares are claimed too"),
    ("decline", "bool", "dismiss the unlisted, non-rare commons"),
    ("combat", "object", "target, rest, monsters"),
    ("stop", "list", "guards that end the run; each may carry a say"),
    ("start", "string", "the first step, defaults to the first one listed"),
    ("steps", "list", "the route itself"),
]

COMBAT_KEYS = [
    ("target", "my target | nearest | weakest"),
    ("rest", "hp percent at which to rest, 0..100"),
    ("monsters", "only fight these names; also switches the target to nearest"),
]

VERBS = [
    ("join", "map, cell, pad, room",
     "Transfer to a map, or walk to the cell when that map is already loaded. A "
     "transfer the client's own cooldown refuses is held and re-sent instead of "
     "burning the step's timeout."),
    ("moveTo", "cell, pad", "Walk to a cell in the map already loaded."),
    ("exit", "id", "Take a map pad by its id."),
    ("exitTo", "cell", "Take the pad that leads to that cell."),
    ("aggro", "none", "Pull every monster in the cell through the game's own "
                      "aggroMons, so no monster id is written down."),
    ("fight", "none", "Hand combat to the engine; it picks targets and casts."),
    ("stopFight", "none", "Stop attacking, and drop the target."),
    ("rest", "none", "Sit down until the client's own rest finishes."),
    ("heal", "none", "Use the heal skill if the class has one."),
    ("equip", "item, safe", "Wear an item by name. safe:false ends the run when "
                            "it is missing; the default only warns."),
    ("boost", "item", "Use a potion by name."),
    ("acceptQuest", "id", "Accept a quest by id, from any map. Followed by a 1.2 s "
                          "settle, because the client marks it accepted before the "
                          "server can refuse."),
    ("completeQuest", "id", "Hand a quest in, from any map."),
    ("quests", "ids", "Ask the server for these quest rows; a route must do this "
                      "before it can read them, and `once` memory only covers what "
                      "it asked for."),
    ("mapItem", "id", "Click a map item by the id the map's own sparkle sends."),
    ("loadShop", "id", "Ask for a shop's rows."),
    ("buy", "item", "Buy one item out of the loaded shop. Goes straight down the "
                    "wire, and parks the shop row the reply handler reads, because "
                    "the client's own call opens a message box a bot cannot dismiss."),
    ("delay", "ms", "Wait, inside the step, 0..600000."),
    ("log", "msg", "Write a line to the log without ending anything."),
    ("stop", "msg", "End the run, with that reason."),
]

CONDITIONS = [
    ("here", "map?, cell?", "In that map, and that cell.", "wait"),
    ("cellEmpty", "none", "No monster is alive in the cell.", "wait"),
    ("elapsed", "value 1..3600", "This many seconds since the step was entered.",
     "wait"),
    ("mobsAtLeast", "value 1..12", "That many monsters are alive in the cell.",
     "wait"),
    ("hpBelow", "value 1..100", "Own hp under that percent.", "wait"),
    ("hpAbove", "value 1..100", "Own hp above that percent.", "wait"),
    ("mpBelow", "value 1..100", "Own mp under that percent.", "wait"),
    ("mpAbove", "value 1..100", "Own mp above that percent.", "wait"),
    ("levelBelow", "value 1..100", "Own level under that.", "wait"),
    ("levelAtLeast", "value 1..100", "Own level at or above that.", "both"),
    ("goldAtLeast", "value", "That much gold in hand.", "both"),
    ("itemAtLeast", "item, value", "That many of an item in the bag.", "both"),
    ("itemBelow", "item, value", "Fewer than that many in the bag.", "wait"),
    ("bagFreeBelow", "value 1..500", "Fewer than that many free bag slots.", "both"),
    ("questActive", "id", "The quest is taken and not ready.", "wait"),
    ("questComplete", "id", "Ready to hand in: the client says so, or every turn-in "
                            "item is held, in the bag or as a temp counter.", "wait"),
    ("questInHand", "id", "Taken, ready or not.", "wait"),
    ("questOffered", "id", "Available to take: not in hand, not already handed in "
                           "this session, not blocked by level or by an earlier "
                           "step of the same chain.", "wait"),
    ("tempAtLeast", "item, value", "That many of a temp item, keyed by name.", "wait"),
    ("shopLoaded", "id", "That shop's rows are in.", "wait"),
    ("classIs", "name", "That class is equipped.", "wait"),
    ("runFor", "value 1..86400", "This many seconds since the run started.", "both"),
    ("droppedItem", "item", "The named item dropped since the last scan.", "stop"),
    ("droppedRarity", "none", "A rare drop landed; Event items do not count.", "stop"),
    ("all", "of", "Every condition in the list holds.", "both"),
    ("any", "of", "At least one condition in the list holds.", "both"),
    ("not", "of", "The condition does not hold.", "both"),
]

STEP_KEYS = [
    ("id", "string", "unique within the preset"),
    ("do", "list of verbs", "run once, when the step is entered"),
    ("wait", "list of conditions", "all of them must hold; empty finishes at once"),
    ("branch", "list of conditions", "first match wins; each carries its own then"),
    ("else", "string", "the step to go to when no branch matches"),
    ("then", "string", "the step to go to when the wait holds"),
    ("timeout", "seconds", "how long the wait may fail; 0 switches the watchdog off"),
    ("retry", "count", "re-entries before the run gives up as stuck"),
    ("hold", "true | {every}", "keep re-running do while the wait fails; `every` is "
                               "the gap in seconds"),
]


# ------------------------------------------------------------------ format

def cond(when, **kw):
    d = {"when": when}
    d.update(kw)
    return d


def plain(x):
    if isinstance(x, dict):
        return {k: plain(v) for k, v in x.items()}
    if isinstance(x, list):
        return [plain(v) for v in x if v is not GAP]
    return x


def render_cond(c, pad):
    if not isinstance(c.get("of"), list):
        return json.dumps(c, ensure_ascii=False)
    head = {k: v for k, v in c.items() if k != "of"}
    text = json.dumps(head, ensure_ascii=False)
    inner = ",\n".join(pad + "  " + render_cond(x, pad + "  ") for x in c["of"])
    return text[:-1] + ', "of": [\n' + inner + "\n" + pad + "]}"


def render_list(key, items, pad):
    def one(x):
        return pad + "  " + render_cond(x, pad + "  ")

    if GAP in items:
        at = items.index(GAP)
        text = ",\n".join(one(x) for x in items[:at])
        text += ",\n\n" + ",\n".join(one(x) for x in items[at + 1:])
        return pad + '"' + key + '": [\n' + text + "\n" + pad + "]"

    body = [one(x) for x in items]
    single = "[" + ", ".join(b.strip() for b in body) + "]"
    if len(pad) + len(key) + len(single) + 4 <= 96:
        return pad + '"' + key + '": ' + single
    return pad + '"' + key + '": [\n' + ",\n".join(body) + "\n" + pad + "]"


def render_step(step):
    pad = "    "
    fields = ['      "id": ' + json.dumps(step["id"])]
    for key in ("branch", "do", "wait"):
        if key in step:
            fields.append(render_list(key, step[key], "      "))
    for key in ("timeout", "retry"):
        if key in step:
            fields.append('      "' + key + '": ' + str(step[key]))
    for key in ("then", "else"):
        if key in step:
            fields.append('      "' + key + '": ' + json.dumps(step[key]))
    return pad + "{\n" + ",\n".join(fields) + "\n" + pad + "}"


ORDER = ["schema", "id", "name", "bundle", "once", "notes", "pickup", "loot",
         "decline", "combat", "stop", "start"]


def render_preset(preset):
    steps = preset["steps"]
    out = ["{"]
    for key in ORDER:
        if key not in preset:
            continue
        value = preset[key]
        if key == "stop":
            body = ",\n".join("    " + json.dumps(c, ensure_ascii=False) for c in value)
            out.append('  "stop": [\n' + body + "\n  ],")
        else:
            out.append("  " + json.dumps(key) + ": " + json.dumps(value, ensure_ascii=False) + ",")
    out.append('  "steps": [')
    body = ",\n".join(render_step(s) for s in steps)
    out.append(body)
    out.append("  ]")
    out.append("}")
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------ routes

def route_step(quests):
    return {
        "id": "route",
        "do": [{"act": "stopFight"},
               {"act": "quests", "ids": [q.id for q in quests]}],
        "wait": [cond("elapsed", value=3)],
        "timeout": 30, "retry": 3, "then": "pick",
    }


def pick_step(quests):
    branch = [cond("questInHand", id=q.id, then=f"q{q.id}") for q in quests]
    branch.append(GAP)
    branch += [cond("questOffered", id=q.id, then=f"q{q.id}") for q in quests]
    return {"id": "pick", "branch": branch, "else": "done"}


def send_step(quest, then):
    return {
        "id": f"q{quest.id}-send",
        "do": [{"act": "stopFight"}, {"act": "completeQuest", "id": quest.id}],
        "wait": [cond("not", of=cond("questComplete", id=quest.id)),
                 cond("elapsed", value=2)],
        "timeout": 20, "retry": 3, "then": then,
    }


def quest_steps(quest, then):
    qid = quest.id
    after = {"fight": f"q{qid}-farm", "map": f"q{qid}-click",
             "multi": f"q{qid}-a"}[quest.kind]
    blank = quest.moves_to_blank()
    if blank:
        after = f"q{qid}-move"

    out = [{
        "id": f"q{qid}",
        "branch": [cond("questComplete", id=qid, then=f"q{qid}-send")],
        "do": [{"act": "acceptQuest", "id": qid},
               {"act": "join", "map": quest.map, "cell": quest.cell, "pad": quest.pad}],
        "wait": [cond("here", map=quest.map, cell=quest.cell),
                 cond("questInHand", id=qid)],
        "timeout": 30, "retry": 3, "then": after,
    }]

    if blank:
        out.append({
            "id": f"q{qid}-move",
            "do": [{"act": "moveTo", "cell": "Blank", "pad": "Bloom"}],
            "wait": [cond("here", map=quest.map, cell="Blank")],
            "timeout": 20, "retry": 3,
            "then": f"q{qid}-click" if quest.kind == MAP else f"q{qid}-a",
        })

    if quest.kind == FIGHT:
        out.append({
            "id": f"q{qid}-farm",
            "branch": [cond("questComplete", id=qid, then=f"q{qid}-send")],
            "do": [{"act": "aggro"}, {"act": "fight"}],
            "wait": [cond("any", of=[cond("questComplete", id=qid),
                                     cond("elapsed", value=15)])],
            "timeout": 0, "then": f"q{qid}-farm",
        })

    elif quest.kind == MAP:
        out.append({
            "id": f"q{qid}-click",
            "branch": [cond("questComplete", id=qid, then=f"q{qid}-send")],
            "do": [{"act": "stopFight"},
                   {"act": "mapItem", "id": quest.items[0]}],
            "wait": [cond("questComplete", id=qid)],
            "timeout": 3, "retry": 60, "then": f"q{qid}-send",
        })

    elif quest.kind == MULTI:
        legs = "abc"[:len(quest.items)]
        for at, leg in enumerate(legs):
            following = legs[(at + 1) % len(legs)]
            out.append({
                "id": f"q{qid}-{leg}",
                "branch": [cond("questComplete", id=qid, then=f"q{qid}-send")],
                "do": [{"act": "stopFight"},
                       {"act": "mapItem", "id": quest.items[at]}],
                "wait": [cond("any", of=[cond("questComplete", id=qid),
                                         cond("elapsed", value=3)])],
                "then": f"q{qid}-{following}",
            })

    out.append(send_step(quest, then))
    return out


def reward_steps(reward):
    owned = [cond("itemAtLeast", item=reward.item, value=1, then="done")]
    return [
        {
            "id": "reward",
            "branch": owned,
            "do": [{"act": "join", "map": reward.map, "cell": "Enter",
                    "pad": "Spawn"}],
            "wait": [cond("here", map=reward.map)],
            "timeout": 45, "retry": 2, "then": "reward-shop",
        },
        {
            "id": "reward-shop",
            "branch": owned,
            "do": [{"act": "loadShop", "id": reward.shop}],
            "wait": [cond("any", of=[cond("shopLoaded", id=reward.shop),
                                     cond("elapsed", value=10)])],
            "timeout": 20, "retry": 1, "then": "reward-buy",
        },
        {
            "id": "reward-buy",
            "branch": owned,
            "do": [{"act": "buy", "item": reward.item}],
            "wait": [cond("any", of=[cond("itemAtLeast", item=reward.item, value=1),
                                     cond("elapsed", value=6)])],
            "timeout": 20, "retry": 1, "then": "done",
        },
    ]


def build(meta, quests):
    preset = {"schema": 1, "start": "route"}
    preset.update(meta)

    reward = preset.pop("reward", None)
    done = preset.pop("done", "route complete: nothing left to accept")
    tail = "reward" if reward else "route"
    steps = [route_step(quests), pick_step(quests)]
    steps.append({"id": "done", "do": [{"act": "stop", "msg": done}]})
    for quest in quests:
        steps += quest_steps(quest, tail if quest is quests[-1] else "route")
    if reward:
        steps += reward_steps(reward)
    preset["steps"] = steps
    return preset


def load_routes():
    out = {}
    for path in sorted(ROUTES.glob("*.py")):
        spec = importlib.util.spec_from_file_location("route_" + path.stem, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        out[path.stem] = (module.PRESET, module.QUESTS)
    return out


def check_quests(label, quests):
    for quest in quests:
        for field in ("id", "kind", "map"):
            if getattr(quest, field) in (None, ""):
                fail(f"{label}: quest {quest.id}: missing {field}")
        if quest.kind not in KINDS:
            fail(f"{label}: quest {quest.id}: unknown kind {quest.kind!r}")
        if quest.kind in (MAP, MULTI) and not quest.items:
            fail(f"{label}: quest {quest.id}: needs map item ids")
        if quest.kind == MULTI and len(quest.items) > 3:
            fail(f"{label}: quest {quest.id}: at most three legs")


def build_all():
    routes = load_routes()
    if not routes:
        fail(f"no routes in {ROUTES}")

    for stem, (meta, quests) in routes.items():
        label = f"{stem}.py"
        if meta.get("id") != stem:
            fail(f"{label}: id must be {stem!r}, the file is the id")
        check_quests(label, quests)

        preset = build(dict(meta), list(quests))
        text = render_preset(preset)
        if json.loads(text) != plain(preset):
            fail(f"{label}: rendered json does not round-trip")

        path = BOTS / f"{stem}.json"
        path.write_text(text, encoding="utf-8")
        print(f"   {path.relative_to(ROOT)}: {len(preset['steps'])} steps, "
              f"{len(text)} bytes")


# -------------------------------------------------------------------- docs

def esc(text):
    return str(text).replace("|", "\\|")


def api_docs():
    out = ["# Bot API", "",
           "Generated by `tools/gen.py --docs` from the catalog in that file. Do not",
           "hand-edit: change the catalog and run it again.", "",
           "## Preset", "", "| key | type | meaning |", "| --- | --- | --- |"]
    out += [f"| `{k}` | {esc(t)} | {esc(text)} |" for k, t, text in PRESET_KEYS]

    out += ["", "`combat` holds:", "", "| key | value |", "| --- | --- |"]
    out += [f"| `{k}` | {esc(v)} |" for k, v in COMBAT_KEYS]

    out += ["", "## Steps", "",
            "A step is a name, some verbs, and a condition that ends it.", "",
            "| key | type | meaning |", "| --- | --- | --- |"]
    out += [f"| `{k}` | {esc(t)} | {esc(text)} |" for k, t, text in STEP_KEYS]
    out += [
        "",
        "A step runs its verbs once, when it is entered. Then its `wait` is",
        "tested on every tick: when it holds, the run goes to `then`, or to the",
        "`then` of the first matching `branch`, or to `else`. A wait that keeps",
        "failing for `timeout` seconds re-enters the step, verbs and all, while",
        "`retry` lasts; after that the run stops with `stuck: <step id>`. A wait",
        "is an AND list, so `[{not questComplete}, {elapsed 2}]` is a two second",
        "floor, not a fallback.",
        "",
        "## Verbs", "", "| verb | arguments | what it does |", "| --- | --- | --- |"]
    out += [f"| `{a}` | {esc(b)} | {esc(c)} |" for a, b, c in VERBS]

    out += ["", "## Conditions", "",
            "A wait and a stop use the same conditions; `stop` accepts only the",
            "rows marked `stop` or `both`, and each of those may carry a `say`",
            "that becomes the reason the run ended.", "",
            "| when | fields | true when | allowed in |", "| --- | --- | --- | --- |"]
    out += [f"| `{a}` | {esc(b)} | {esc(c)} | {d} |" for a, b, c, d in CONDITIONS]

    out += [
        "",
        "## Writing a route",
        "",
        "A story is one line per quest. `tools/routes/<id>.py` holds `PRESET` and",
        "`QUESTS`; `tools/gen.py` writes `bots/<id>.json` from them:",
        "",
        "```python",
        "from gen import Quest, Reward, FIGHT, MAP, MULTI",
        "",
        "PRESET = {",
        '    "id": "chaos1",',
        '    "name": "1st Chaos Lord \\u00b7 Chiral Valley",',
        '    "bundle": False,',
        '    "once": True,',
        '    "notes": "what the route does and why",',
        '    "pickup": True,',
        '    "combat": {"target": "nearest", "rest": 60},',
        '    "stop": [{"when": "bagFreeBelow", "value": 2, "say": "bag almost full"}],',
        '    "reward": Reward(map="freakitiki", shop=946, item="Phoenix Hunter"),',
        "}",
        "",
        "QUESTS = [",
        '    Quest(245, FIGHT, "mobius", "New5", "Left"),',
        '    Quest(246, MAP, "mobius", "Enter", "Spawn", items=[42], blank=False),',
        '    Quest(271, MULTI, "hydra", "Enter", "Spawn", items=[52, 51, 50]),',
        "]",
        "```",
        "",
        "What it builds: `route` asks the server for every quest row, `pick` takes",
        "whatever is in hand or next to be offered, and each quest expands into",
        "accept-and-walk, farm or click, turn-in. `MULTI` cycles its ids, which is",
        "what a quest with more than one map item needs. `once` routes remember",
        "what they handed in, so `pick` leaves a finished quest alone and the run",
        "ends itself when nothing is left. `done` replaces the message it ends",
        "with; `reward` appends a shop visit, and a step there goes straight to",
        "`done` when the item is already owned.",
        "",
        "Two rules the generated steps already follow, worth keeping if you write",
        "one by hand: a quest that reads complete is handed in before combat",
        "restarts, and a click is sent from the Blank cell, where nothing can",
        "reach the character.",
        "",
        "**Map items.** A `getMapItem` packet is `<room> % <id>`, and `mapItem`",
        "wants the second number: the id the map's own sparkle carries. The first",
        "is the room the recorder happened to be in and means nothing to anyone",
        "else. The id belongs to a map revision, so if a click does nothing the",
        "map file has changed and the id has to be read out of it again.",
        "",
        "**Story memory.** `once` keeps the quests a route has handed in for the",
        "session only, per character: nothing is written to disk, and the Bots tab",
        "can forget it. A one-time quest whose slot counter has already caught up",
        "is treated as done too, which is what lets a restart continue a chain",
        "instead of redoing it.",
        "",
        "```",
        "python3 tools/gen.py             # rebuild bots/*.json",
        "python3 tools/gen.py --docs      # rebuild this file",
        "python3 tools/gen.py --check     # diff the catalog against the client",
        "python3 build_index.py --push    # publish",
        "```",
        "",
    ]
    return "\n".join(out)


# ------------------------------------------------------------------- check

def app_catalog():
    """The client's own validator lists, when this repo sits inside a checkout."""
    path = ROOT.parent.parent / "build" / "bots.py"
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("client_bots", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return {
        "verbs": set(module.VERBS),
        "waits": set(module.WAITS),
        "stops": set(module.STOPS),
        "keys": set(module.TOP_KEYS),
    }


def check_catalog():
    app = app_catalog()
    if app is None:
        print("   no client checkout next to this repo, catalog not compared")
        return

    waits = {c[0] for c in CONDITIONS if c[3] != "stop"}
    stops = {c[0] for c in CONDITIONS if c[3] != "wait"}
    preset_keys = {k for k, _, _ in PRESET_KEYS}

    pairs = [
        ("verbs", {v[0] for v in VERBS}, app["verbs"]),
        ("waits", waits, app["waits"]),
        ("stops", stops, app["stops"]),
        ("preset keys", preset_keys, app["keys"]),
    ]
    bad = False
    for label, mine, theirs in pairs:
        if mine == theirs:
            continue
        bad = True
        for name in sorted(theirs - mine):
            print(f"   {label}: {name!r} is in the client, not in the catalog")
        for name in sorted(mine - theirs):
            print(f"   {label}: {name!r} is in the catalog, not in the client")
    if bad:
        fail("catalog is out of step with the client's validator")
    print("   catalog matches the client's validator")


def fail(message):
    print(f"gen error: {message}", file=sys.stderr)
    sys.exit(1)


def main(argv):
    sys.path.insert(0, str(TOOLS))
    want = set(argv) or {"build"}
    if want & {"-h", "--help"}:
        print(__doc__)
        return

    if "build" in want:
        build_all()
    if "--docs" in want:
        DOCS.mkdir(exist_ok=True)
        path = DOCS / "bot-api.md"
        path.write_text(api_docs(), encoding="utf-8")
        print(f"   {path.relative_to(ROOT)}")
    if "--check" in want:
        check_catalog()


if __name__ == "__main__":
    main(sys.argv[1:])
