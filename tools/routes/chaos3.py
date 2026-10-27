"""The 3rd Chaos Lord line, quests 319 through 363, in play order."""

from gen import Quest, Reward, FIGHT, MAP, HUNT, META

NOTES = (
    "The whole 3rd Chaos Lord line in one run: the pines and tavern chain that "
    "opens Dwarfhold, the dwarfhold quests themselves, the upper city, and the "
    "prison break that ends with Dragonlord Vath. It is a one-pass route "
    "(`once`), so a quest this character has handed in is remembered and never "
    "taken again, and the run stops itself once nothing is left; each pass works "
    "on whatever is already in hand, otherwise the next quest of the chain the "
    "server actually offers, so a restart picks up where the character is. Six "
    "of the 36 are not fights: 319, 337, 344, 346, 362 and 363 are map items, "
    "clicked by the id the map's own sparkle sends, on a loop until the quest "
    "asks for nothing. 319 clicks from the tavern's spawn cell; the rest stop "
    "combat and stand on the Blank cell first, where nothing can reach them, "
    "because a click is a packet and does not need the sparkle in sight. 353 and "
    "356 are hunts: their turn-ins want counters paid in different cells, so the "
    "route walks between r9 and r8 and farms whichever counter is still short "
    "instead of sitting in one room forever. 323, 343, 354 and 357 are turn-ins "
    "that only want a temp item the line pays earlier, so their check sends the "
    "character back to 327, 340, 353 and 356 rather than waiting on a counter "
    "that will never arrive. A fight step hands over the moment the quest reads "
    "complete rather than finishing the mob, and every turn-in stops combat "
    "first, so a finished quest never keeps the boss angry. Loot is claimed as it "
    "falls (`pickup`): these quests pay real drops with names a route cannot list "
    "ahead of time. The last steps buy the Volcanic Fire Sword from shop 947, "
    "the line's proof item, and end quietly if that shop is not unlocked."
)

PRESET = {
    "id": "chaos3",
    "name": "3rd Chaos Lord \u00b7 Dwarfhold Vath",
    "bundle": False,
    "once": True,
    "notes": NOTES,
    "pickup": True,
    "combat": {"target": "nearest", "rest": 60},
    "stop": [
        {"when": "bagFreeBelow", "value": 2, "say": "bag almost full"},
        {"when": "runFor", "value": 21600, "say": "six hours on this route"},
    ],
    "done": "3rd Chaos Lord complete: nothing left to accept",
    "reward": Reward(map="freakitiki", shop=947, item="Volcanic Fire Sword"),
}

QUESTS = [
    Quest(319, MAP, "tavern", "Enter", "Spawn", items=[56], blank=False),
    Quest(320, FIGHT, "pines", "Tavern", "Left"),
    Quest(321, FIGHT, "pines", "Mountain", "Right"),
    Quest(322, FIGHT, "pines", "Boss", "Right"),
    Quest(324, FIGHT, "pines", "Mountain", "Right"),
    Quest(325, FIGHT, "pines", "Tavern", "Left"),
    Quest(326, FIGHT, "pines", "Citadel", "Left"),
    Quest(327, FIGHT, "pines", "Enter", "Spawn"),
    Quest(323, META, "tavern", "Enter", "Spawn",
          needs=[("Snowbeard's Gold", 327)]),
    Quest(344, MAP, "dwarfhold", "r1", "Left", items=[60]),
    Quest(331, FIGHT, "mountainpath", "Enter", "Spawn"),
    Quest(332, FIGHT, "mountainpath", "r3", "Left"),
    Quest(333, FIGHT, "dwarfhold", "r2", "Left"),
    Quest(334, FIGHT, "dwarfhold", "r1", "Left"),
    Quest(335, FIGHT, "dwarfhold", "Enter", "Spawn"),
    Quest(336, FIGHT, "dwarfhold", "rdoor", "Left"),
    Quest(337, MAP, "dwarfhold", "r4", "Left", items=[59]),
    Quest(338, FIGHT, "dwarfhold", "r2", "Right"),
    Quest(339, FIGHT, "dwarfhold", "r3", "Right"),
    Quest(340, FIGHT, "dwarfhold", "Enter", "Spawn"),
    Quest(343, META, "dwarfhold", "rdoor", "Left",
          needs=[("Upper City Key", 340)]),
    Quest(341, FIGHT, "dwarfhold", "rmole", "Right"),
    Quest(346, MAP, "uppercity", "Enter", "Spawn", items=[61]),
    Quest(347, FIGHT, "uppercity", "r1", "Right"),
    Quest(348, FIGHT, "uppercity", "r5", "Left"),
    Quest(349, FIGHT, "uppercity", "r3", "Right"),
    Quest(350, FIGHT, "uppercity", "r4", "Left"),
    Quest(351, FIGHT, "uppercity", "r6", "Left"),
    Quest(352, FIGHT, "uppercity", "r7", "Left"),
    Quest(353, HUNT, "dwarfprison", "Enter", "Spawn",
          needs=[("Balboa Core", 4, "r9", "Right"),
                 ("Rusted Claw", 3, "r9", "Right"),
                 ("Magnesium Flare", 1, "r8", "Right")]),
    Quest(354, META, "dwarfprison", "Enter", "Spawn",
          needs=[("Thermite", 353)]),
    Quest(355, FIGHT, "dwarfprison", "Warden", "Right"),
    Quest(356, HUNT, "dwarfprison", "Warden", "Right",
          needs=[("Flint Stone", 2, "r9", "Right"),
                 ("Nitrate Elements", 3, "r9", "Right"),
                 ("Drow Shoelaces", 3, "r8", "Right")]),
    Quest(357, META, "dwarfprison", "r10", "Right",
          needs=[("Tee-En-Tee", 356)]),
    Quest(362, MAP, "roc", "Enter", "Spawn", items=[62]),
    Quest(363, MAP, "stalagbite", "Enter", "Spawn", items=[63]),
]
