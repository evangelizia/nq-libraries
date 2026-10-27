"""The 2nd Chaos Lord line, quests 2909 through 3189, in play order."""

from gen import Quest, FIGHT, MAP, TALK, MIX, META

NOTES = (
    "The whole 2nd Chaos Lord line in one run: the mirror chains in /battleoff, "
    "/brightfall and /overworld, then Bardolph's seven in /reddeath, then the "
    "three ingredients of the Shriekward Potion and the two beasts in "
    "/mirrorportal. It is a one-pass route (`once`), so a quest this character has "
    "handed in is remembered and never taken again, and the run stops itself once "
    "nothing is left; each pass works on whatever is already in hand, otherwise "
    "the next quest of the chain the server actually offers, so a restart picks up "
    "where the character is. Nine of the 38 are not fights: 2909, 2910, 2915, 2916, "
    "2923, 2927, 2931, 3168 and 3183 are map items, clicked by the id the map's own "
    "sparkle sends, on a loop until the quest asks for nothing. Those stop combat "
    "and stand on the Blank cell first, except 3183, which clicks from the town's "
    "spawn cell: a click is a packet and does not need the sparkle in sight. 2918 "
    "is a talk: it is ready the moment the character walks into /overworld, so its "
    "step waits for that rather than for a fight. 3167 wants five Boneweed before it wants its two "
    "incenses, so it farms first and clicks after, in one step pair. 3184, 3185 and "
    "3186 are the three ingredients, and each pays its counter by chance, so the "
    "route takes the quest again until the counter lands instead of handing in a "
    "potion it cannot make; 3187 is the turn-in that wants all three, so it is "
    "accepted first and its check step sends the character to whichever counter is "
    "still missing, which is the order the reference bot runs them in. 3188 needs "
    "the potion worn, so its step equips it and only warns when the bag has none. "
    "A fight step hands over the moment the quest reads complete rather than "
    "finishing the mob, and every turn-in stops combat first, so a finished quest "
    "never keeps the boss angry. Loot is claimed as it falls (`pickup`): these "
    "quests pay real drops with names a route cannot list ahead of time. 3173 and "
    "3174 are side quests the line does not need."
)

PRESET = {
    "id": "chaos2",
    "name": "2nd Chaos Lord \u00b7 Mirror Portal",
    "bundle": False,
    "once": True,
    "notes": NOTES,
    "pickup": True,
    "combat": {"target": "nearest", "rest": 60},
    "stop": [
        {"when": "bagFreeBelow", "value": 2, "say": "bag almost full"},
        {"when": "runFor", "value": 21600, "say": "six hours on this route"},
    ],
    "done": "2nd Chaos Lord complete: nothing left to accept",
}

QUESTS = [
    Quest(2909, MAP, "battleoff", "Enter", "Spawn", items=[1779]),
    Quest(2910, MAP, "battleoff", "Enter", "Spawn", items=[1780]),
    Quest(2911, FIGHT, "battleoff", "r7", "Right"),
    Quest(2912, FIGHT, "battleoff", "r7", "Right"),
    Quest(2913, FIGHT, "brightfall", "r4", "Left"),
    Quest(2914, FIGHT, "brightfall", "r1", "Left"),
    Quest(2915, MAP, "brightfall", "Enter", "Spawn", items=[1781]),
    Quest(2916, MAP, "brightfall", "Enter", "Spawn", items=[1782]),
    Quest(2917, FIGHT, "brightfall", "r3", "Left"),
    Quest(2918, TALK, "overworld", "Enter", "Spawn"),
    Quest(2919, FIGHT, "overworld", "Enter", "Spawn"),
    Quest(2920, FIGHT, "overworld", "Enter", "Spawn"),
    Quest(2921, FIGHT, "overworld", "Enter", "Spawn"),
    Quest(2922, FIGHT, "overworld", "r2", "Up"),
    Quest(2923, MAP, "overworld", "Enter", "Spawn", items=[1800]),
    Quest(2924, FIGHT, "overworld", "r6", "Left"),
    Quest(2925, FIGHT, "overworld", "r6", "Left"),
    Quest(2926, FIGHT, "overworld", "r6", "Left"),
    Quest(2927, MAP, "overworld", "Enter", "Spawn", items=[1801]),
    Quest(2928, FIGHT, "overworld", "Enter", "Spawn"),
    Quest(2929, FIGHT, "overworld", "Enter", "Spawn"),
    Quest(2930, FIGHT, "overworld", "Enter", "Spawn"),
    Quest(2931, MAP, "overworld", "Enter", "Spawn", items=[1802]),
    Quest(2932, FIGHT, "overworld", "boss1", "Left"),
    Quest(3166, FIGHT, "reddeath", "r2", "Left"),
    Quest(3167, MIX, "reddeath", "r3", "Left", items=[2178, 2179],
          drop=("Boneweed", 5)),
    Quest(3168, MAP, "reddeath", "Enter", "Spawn", items=[2180]),
    Quest(3169, FIGHT, "reddeath", "r7", "Down"),
    Quest(3170, FIGHT, "reddeath", "r7", "Down"),
    Quest(3171, FIGHT, "reddeath", "r5", "Right"),
    Quest(3172, FIGHT, "reddeath", "r5", "Right"),
    Quest(3183, MAP, "battleontown", "Enter", "Spawn", items=[2203], blank=False),
    Quest(3187, META, "mirrorportal", needs=[("Perfect Prism", 3184),
                                             ("Unchaorrupted Sample", 3185),
                                             ("Harpy Feather", 3186)]),
    Quest(3184, FIGHT, "earthstorm", "r7", "Right", roll="Perfect Prism",
          then="q3187"),
    Quest(3185, FIGHT, "bloodtuskwar", "r10", "Down",
          roll="Unchaorrupted Sample", then="q3187"),
    Quest(3186, FIGHT, "bloodtuskwar", "r5", "Down", roll="Harpy Feather",
          then="q3187"),
    Quest(3188, FIGHT, "mirrorportal", "r3", "Left", gear="Shriekward Potion"),
    Quest(3189, FIGHT, "mirrorportal", "r4", "Left"),
]
