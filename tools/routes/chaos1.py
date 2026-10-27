"""The 1st Chaos Lord line, quests 245 through 272, in play order."""

from gen import Quest, Reward, FIGHT, MAP, MULTI

NOTES = (
    "The whole 1st Chaos Lord line in one run: the five Chiral chains in /mobius, "
    "/faerie, /cornelis, /relativity and /hydra, then Escherion himself, then the "
    "Phoenix Hunter the saga pays out. It is a one-pass route (`once`), so a quest "
    "this character has handed in is remembered and never taken again, and the run "
    "stops itself once nothing is left; each pass works on whatever is already in "
    "hand, otherwise the next quest of the chain the server actually offers, so a "
    "restart picks up where the character is. Nine of the 26 are not fights: 246, "
    "251, 260, 261, 262, 263, 266, 267 and 271 are map items, clicked by the id the "
    "map's own sparkle sends, on a loop until the quest asks for nothing. Those stop "
    "combat and stand on the Blank cell first, where nothing can reach them, because "
    "a click is a packet and does not need the sparkle in sight; 271 wants three "
    "items, so it cycles through 52, 51 and 50 instead of waiting on one. A fight "
    "step hands over the moment the quest reads complete rather than finishing the "
    "mob, and every turn-in stops combat first, so a finished quest never keeps the "
    "boss angry. Loot is claimed as it falls (`pickup`): these quests pay real drops "
    "with names a route cannot list ahead of time. The last steps buy the free "
    "Phoenix Hunter from shop 946 in /freakitiki, the saga's own reward; if the shop "
    "is not unlocked the route ends quietly instead of stalling on it. 253 and 254 "
    "are side quests the line does not need."
)

PRESET = {
    "id": "chaos1",
    "name": "1st Chaos Lord \u00b7 Chiral Valley",
    "bundle": False,
    "once": True,
    "notes": NOTES,
    "pickup": True,
    "combat": {"target": "nearest", "rest": 60},
    "stop": [
        {"when": "bagFreeBelow", "value": 2, "say": "bag almost full"},
        {"when": "runFor", "value": 21600, "say": "six hours on this route"},
    ],
    "done": "Chaos Lord complete: nothing left to accept",
    "reward": Reward(map="freakitiki", shop=946, item="Phoenix Hunter"),
}

QUESTS = [
    Quest(245, FIGHT, "mobius", "New5", "Left"),
    Quest(246, MAP, "mobius", "Enter", "Spawn", items=[42], blank=False),
    Quest(247, FIGHT, "relativity", "Side3", "Left"),
    Quest(260, MAP, "mobius", "Enter", "Spawn", items=[44], blank=False),
    Quest(248, FIGHT, "mobius", "New6", "Right"),
    Quest(249, FIGHT, "mobius", "Slugfit", "Spawn"),
    Quest(250, FIGHT, "faerie", "Side3", "Left"),
    Quest(251, MAP, "faerie", "Side2", "Left", items=[43]),
    Quest(252, FIGHT, "faerie", "Side3", "Left"),
    Quest(255, FIGHT, "faerie", "End", "Center"),
    Quest(256, FIGHT, "faerie", "TopRock", "Center"),
    Quest(257, FIGHT, "cornelis", "Side4", "Right"),
    Quest(261, MAP, "cornelis", "Enter", "Spawn", items=[45]),
    Quest(258, FIGHT, "cornelis", "Side4", "Right"),
    Quest(262, MAP, "cornelis", "Enter", "Spawn", items=[46]),
    Quest(259, FIGHT, "cornelis", "Side5", "Center"),
    Quest(263, MAP, "cornelis", "Enter", "Spawn", items=[47]),
    Quest(266, MAP, "mobius", "Enter", "Spawn", items=[48]),
    Quest(267, MAP, "mobius", "Enter", "Spawn", items=[49]),
    Quest(264, FIGHT, "mobius", "New6", "Right"),
    Quest(265, FIGHT, "faerie", "Side3", "Left"),
    Quest(268, FIGHT, "relativity", "Side2", "Left"),
    Quest(269, FIGHT, "relativity", "Side2", "Right"),
    Quest(270, FIGHT, "relativity", "Side5", "Right"),
    Quest(271, MULTI, "hydra", "Enter", "Spawn", items=[52, 51, 50]),
    Quest(272, FIGHT, "escherion", "Boss", "Left"),
]
