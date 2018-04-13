import ship_stats
import random

def get_weight(ship):
    return (10 - ship.rarity) * (20 - ship.rarity)

# TODO maybe add more options or focii for randomization
def get_random_drop(owner):
    ships = ship_stats.get_all_ships(allow_remodel=False)

    total_pool = sum(get_weight(s) for s in ships)
    val = random.randrange(total_pool)
    for ship in ships:
        val -= get_weight(ship)
        if (val <= 0):
            return ship_stats.ShipInstance.new(ship.sid, owner)
            break
    return ship_stats.ShipInstance.new(11, owner)

def get_drop_chances():
    ships = ship_stats.get_all_ships(allow_remodel=False)

    total_pool = sum(get_weight(s) for s in ships)
    totals = [0] * 8
    for rarity in range(8):
        rtotal = sum(get_weight(s) for s in ships if s.rarity == rarity + 1)
        totals[rarity] = rtotal
    return list(map(lambda x: x / total_pool, totals))
