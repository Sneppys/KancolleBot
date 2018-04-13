import ship_stats
import random
import sqlite3
import os
import time
import userinfo

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
DB_PATH = os.path.join(DIR_PATH, "../usersdb.db") # hidden to git

def get_connection():
    return sqlite3.connect(DB_PATH)

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


DROP_COOLDOWN = 30

def drop_resources(did):
    query = "SELECT Last_Bonus FROM Users WHERE DiscordID='%s';" % (did)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query)
    ts = cur.fetchall()[0][0]
    cur.close()

    drop = False
    if (ts + DROP_COOLDOWN < time.time()):
        drop = True

        new_time = int(time.time())
        query = "UPDATE Users SET Last_Bonus='%s' WHERE DiscordID='%s';" % (new_time, did)
        cur = conn.cursor()
        cur.execute(query)
        cur.close()
    conn.commit()

    if (drop):
        user = userinfo.get_user(did)
        user.mod_fuel(random.randrange(30) + 30)
        user.mod_ammo(random.randrange(30) + 30)
        user.mod_steel(random.randrange(30) + 30)
        user.mod_bauxite(random.randrange(20) + 10)
