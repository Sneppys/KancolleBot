import ship_stats
import random
import sqlite3
import os
import userinfo

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
DB_PATH = os.path.join(DIR_PATH, "../usersdb.db") # hidden to git

def get_connection():
    return sqlite3.connect(DB_PATH)

def get_basic_weight(ship):
    return (9 - ship.rarity) * (10 - ship.rarity) ** 2

def get_random_drop(owner, cur=None, weight_function=get_basic_weight, only_droppable=False, only_craftable=False):
    ships = ship_stats.get_all_ships(cur=cur, allow_remodel=False, only_droppable, only_craftable)

    total_pool = sum(weight_function(s) for s in ships)
    val = random.randrange(total_pool)
    for ship in ships:
        val -= weight_function(ship)
        if (val <= 0):
            return ship_stats.ShipInstance.new(ship.sid, owner)
            break
    return ship_stats.ShipInstance.new(11, owner)

def get_drop_chances(weight_function=get_basic_weight):
    ships = ship_stats.get_all_ships(allow_remodel=False)

    total_pool = sum(weight_function(s) for s in ships)
    totals = [0] * 8
    for rarity in range(8):
        rtotal = sum(weight_function(s) for s in ships if s.rarity == rarity + 1)
        totals[rarity] = rtotal
    return list(map(lambda x: x / total_pool, totals))


DROP_COOLDOWN = 60

def drop_resources(did):
    if (userinfo.check_cooldown(did, 'Last_Bonus', DROP_COOLDOWN) == 0):
        user = userinfo.get_user(did)
        user.mod_fuel(random.randrange(30) + 30)
        user.mod_ammo(random.randrange(30) + 30)
        user.mod_steel(random.randrange(30) + 30)
        user.mod_bauxite(random.randrange(20) + 10)
