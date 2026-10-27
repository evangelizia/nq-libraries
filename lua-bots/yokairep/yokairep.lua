-- Yokai Reputation: the repeatable Pockey Challenge at /dragonkoiz, until
-- Yokai reaches rank 10.
--
-- The recording opens the way in first. A character still on the boat does 380,
-- 381 and 382, which is what lets it into the map; one already past them finds
-- nothing there to take and goes straight to the koi. The rep quest itself is
-- never worked out of quest data: it is accepted, farmed at the cell the
-- recording stands on and handed in as soon as the client calls it complete,
-- and the rank is the only exit, because a repeatable quest never stops being
-- offered.
--
-- The manifest owns the name, the combat settings, the loot and the guards;
-- this file is the route.
--
-- A move is only a packet. The client writes the cell it asked for the moment
-- the packet leaves, so arrival is read from the map's own frame (at_cell), a
-- pad the target cell does not have is answered by trying the next one, and a
-- cell that refuses every pad is reached by re-entering the room there.
--
-- No closures over outer locals: the VM has no upvalues, so shared state is
-- global and a function literal is bound to a name before it is passed on.

RANK = 10
FACTION = "Yokai"
DONE = 0

function at_rank()
    return RANK <= rank(FACTION)
end

function say_rank(where)
    log("info", FACTION .. " rank " .. rank(FACTION) .. "/" .. RANK .. " " .. where)
end

-- A counter may arrive as a temp item or as a bag drop.
function have(name)
    local t = temp(name)
    local i = item(name)
    if i > t then
        return i
    end
    return t
end

-- The pads worth trying, the caller's own first because a recorded leg knows it.
function pad_of(i, first)
    if i == 1 then
        if first == nil or first == "" then
            return "Left"
        end
        return first
    end
    if i == 2 then
        return "Left"
    end
    if i == 3 then
        return "Spawn"
    end
    if i == 4 then
        return "Right"
    end
    if i == 5 then
        return "Center"
    end
    if i == 6 then
        return "Down"
    end
    return "Up"
end

-- Walk to a cell and wait for the map to show it. A pad the cell does not
-- have is refused, so the next one is tried; when every pad is refused the
-- room is re-entered at the cell, which the server does in one step.
function walk(c, p)
    if c == nil or c == "" then
        return true
    end
    if at_cell(c) then
        return true
    end

    log("info", "walk " .. c .. " from " .. cell() .. " on " .. map())

    local i = 1
    while i <= 7 do
        move(c, pad_of(i, p))
        local t = now()
        while not at_cell(c) and now() - t < 2500 do
            yield_tick()
        end
        if at_cell(c) then
            return true
        end
        i = i + 1
    end

    log("warn", map() .. ": " .. c .. " refused every pad, re-entering")
    rejoin(c, p)
    local t = now()
    while not at_cell(c) and now() - t < 10000 do
        yield_tick()
    end
    return at_cell(c)
end

-- Enter a map with a deadline, re-sending the join every few seconds: a
-- transfer the server drops must not end the run. True means the room is up.
function enter(m, c, p, ms)
    if at_map(m) then
        return true
    end

    local t = now()
    local at = 0
    while not at_map(m) and now() - t < ms do
        if at == 0 or 3000 < now() - at then
            at = now()
            join(m, c, p)
        end
        yield_tick()
    end
    if not at_map(m) then
        return false
    end
    sleep(600)
    return true
end

-- Enter the map at the leg's cell, or walk to it when the map is already up.
function go(m, c, p)
    if not enter(m, c, p, 45000) then
        return false
    end
    return walk(c, p)
end

-- Farm one leg until the client calls the quest complete. The counter is read
-- for the panel, not for the exit: a name the server spells differently would
-- otherwise be a farm that never ends, and the quest's own state is the one
-- answer that cannot be wrong. A leg that makes no progress for five minutes
-- fails with the cell it was given, so a wrong cell names itself.
function farm(id, label, m, c, p, counter, need)
    if not go(m, c, p) then
        fail(label .. ": cannot reach " .. c .. " on " .. m)
    end

    local tracked = counter ~= nil and counter ~= ""
    local last = 0
    if tracked then
        last = have(counter)
        log("info", label .. ": " .. counter .. " " .. last .. "/" .. need
            .. " at " .. m .. "/" .. c)
    else
        log("info", label .. ": farming " .. m .. "/" .. c)
    end

    local pull = now()
    local since = now()
    local idle = 0

    while true do
        if ready(id) then
            return
        end

        if not at_cell(c) then
            walk(c, p)
        end

        if mobs() == 0 or 20000 < now() - pull then
            aggro()
            pull = now()
        end
        fight()
        yield_tick()

        if tracked then
            local got = have(counter)
            if last < got then
                last = got
                since = now()
                idle = 0
                log("info", label .. ": " .. counter .. " " .. got .. "/" .. need)
            elseif 20000 < now() - since then
                since = now()
                idle = idle + 1
                if 14 < idle then
                    fail(label .. ": no " .. counter .. " in " .. c)
                end
            end
        elseif 300000 < now() - since then
            since = now()
            idle = idle + 1
            if 3 < idle then
                fail(label .. ": nothing on " .. c .. " in 20 minutes")
            end
        end
    end
end

-- A sparkle is a packet, so it is clicked from the Blank cell where it cannot
-- be interrupted.
function click(m, item)
    if not enter(m, "Enter", "Spawn", 45000) then
        fail("cannot reach " .. m .. " to click")
    end
    walk("Blank", "Bloom")
    stop_fight(false)
    map_item(item)
    sleep(1500)
end

-- A turn-in is polled for four seconds, then sent again, four times before
-- the run gives up. The second send reloads the quest first: a turn-in the
-- client thinks failed can be one the server took.
function send(id, label)
    local n = 0
    while ready(id) do
        n = n + 1
        if 3 < n then
            local why = notice()
            if why == "" then
                fail(label .. " will not turn in")
            end
            fail(label .. " will not turn in: " .. why)
        end
        if n == 2 then
            quests(id)
        end
        stop_fight(false)
        turn_in(id)
        local t = now()
        while ready(id) and now() - t < 4000 do
            yield_tick()
        end
        sleep(800)
    end
    DONE = DONE + 1
end

-- One quest: hand in what is complete, work what is in hand, take what the
-- server offers, and leave alone what is neither.
function quest(id, name, body)
    if ready(id) then
        section(name)
        send(id, name)
        return
    end

    if not in_hand(id) then
        if not offered(id) then
            return
        end
        accept(id)
        local t = now()
        while not in_hand(id) and now() - t < 15000 do
            yield_tick()
        end
        if not in_hand(id) then
            log("warn", name .. ": accept did not stick")
            return
        end
    end

    section(name)
    body()

    local t = now()
    while not ready(id) and now() - t < 60000 do
        yield_tick()
    end
    if ready(id) then
        send(id, name)
    else
        log("warn", name .. ": unfinished on this pass")
    end
end

-- The boat line, as recorded: the Kappa on the war deck, the sail permit on
-- r4, then the finalist medal clicked on the dragonkoi.
function story()
    b = function()
        farm(380, "Turtle Power", "yokaiboat", "War", "Left", "", 0)
    end
    quest(380, "Turtle Power", b)

    b = function()
        farm(381, "Setting Sail to Yokai", "yokaiboat", "r4", "Left", "", 0)
    end
    quest(381, "Setting Sail to Yokai", b)

    b = function()
        click("dragonkoi", 66)
    end
    quest(382, "Tournament Finalist", b)
end

-- The rep cycle. Returns true only when the rank is reached: anything else is
-- the map not being open yet, which the driver answers by working the boat.
function rep()
    local r = rank(FACTION)
    if RANK <= r then
        return true
    end

    section("Yokai rep")
    if not go("dragonkoiz", "Enter", "Spawn") then
        log("warn", "dragonkoiz did not open")
        return false
    end

    while not at_rank() do
        if not in_hand(383) then
            quests(383)
            sleep(1200)
            if not offered(383) then
                log("warn", "Pockey Challenge is not offered here")
                return false
            end
            accept(383)
            local t = now()
            while not in_hand(383) and now() - t < 8000 do
                yield_tick()
            end
            if not in_hand(383) then
                log("warn", "Pockey Challenge accept did not stick")
                return false
            end
        end

        section("Pockey Challenge")
        farm(383, "Pockey Challenge", "dragonkoiz", "t1", "Left", "Piece of Pockey", 3)
        send(383, "Pockey Challenge")
        say_rank("after turn-in")
    end

    return true
end

section("Yokai / reputation")
say_rank("at the start")

if at_rank() then
    done("Yokai is already rank " .. rank(FACTION))
end

quests(383, 380, 381, 382)
sleep(2500)

-- Try the rep cycle first: a character past the boat line is already let in,
-- and a refused accept is the cheapest way to find out. The boat line is the
-- fallback, one pass at a time until the map takes the quest, then the rep
-- cycle owns the run.
if not rep() then
    local pass = 0
    local stuck = 0
    while pass < 12 do
        pass = pass + 1
        local before = DONE
        story()
        sleep(2000)
        if DONE == before then
            stuck = stuck + 1
            if 1 < stuck then
                break
            end
            sleep(3000)
        else
            stuck = 0
            sleep(1500)
        end
        if rep() then
            break
        end
    end
end

say_rank("at the end")
if at_rank() then
    done("Yokai rank " .. rank(FACTION))
end
fail("Yokai is still rank " .. rank(FACTION))
