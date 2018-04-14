import sqlite3
import os
import ship_stats
import sqlutils

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
DB_PATH = os.path.join(DIR_PATH, "../usersdb.db") # hidden to git

USER_TABLE_NAME = "INV_%s"
BASIC_TABLE_NAME = "INV_BASIC"

RESOURCE_CAP = 99999 # max # of any resource a user can have

class User:
    def __init__(self, did, fuel, ammo, steel, bauxite, totalxp):
        self.did = did
        self.fuel = fuel
        self.ammo = ammo
        self.steel = steel
        self.bauxite = bauxite
        self.totalxp = totalxp

    def set_col(self, col, val):
        query = "UPDATE Users SET ?=? WHERE DiscordID=?"
        args = (col, val, self.did)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, args)
        cur.close()
        conn.commit()

    def mod_fuel(self, delta):
        self.fuel += delta
        self.fuel = max(0, min(RESOURCE_CAP, self.fuel))
        self.set_col("RFuel", self.fuel)

    def mod_ammo(self, delta):
        self.ammo += delta
        self.ammo = max(0, min(RESOURCE_CAP, self.ammo))
        self.set_col("RAmmo", self.ammo)

    def mod_steel(self, delta):
        self.steel += delta
        self.steel = max(0, min(RESOURCE_CAP, self.steel))
        self.set_col("RSteel", self.steel)

    def mod_bauxite(self, delta):
        self.bauxite += delta
        self.bauxite = max(0, min(RESOURCE_CAP, self.bauxite))
        self.set_col("RBauxite", self.bauxite)

class UserInventory:
    def __init__(self, did):
        self.did = did
        self.inventory = []

    def append(self, ship_instance):
        self.inventory.append(ship_instance)

    def add_to_inventory(self, ship_instance):
        table_name = USER_TABLE_NAME % (self.did)
        query = "INSERT INTO ? (ShipID) VALUES (?);"
        args = (table_name, ship_instance.sid)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, args)
        cur.close()
        conn.commit()
        self.append(ship_instance)

    def remove_from_inventory(self, inv_id):
        table_name = USER_TABLE_NAME % (self.did)
        query = "DELETE FROM ? WHERE ID=?;"
        args = (table_name, inv_id)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, args)
        cur.close()
        conn.commit()
        ins = [x for x in self.inventory if x.invid == inv_id]
        if (len(ins) > 0):
            si = ins.pop()
            self.inventory.remove(si)

def get_connection():
    return sqlite3.connect(DB_PATH)


def get_user(discordid):
    query = "SELECT * FROM Users WHERE DiscordID=?;"
    args = (discordid,)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, args)
    data = cur.fetchall()
    cur.close()
    conn.commit()

    if (len(data) == 0):
        # if user doesn't exist, create it
        query = "REPLACE INTO Users (DiscordID) VALUES (%s);"
        args = (discordid,)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, args)
        cur.close()
        conn.commit()
        return get_user(discordid)
    row = data[0]
    return User(row[0], row[1], row[2], row[3], row[4], row[6])

def get_user_inventory(discordid):
    table_name = USER_TABLE_NAME % discordid
    if (sqlutils.table_exists(get_connection(), table_name)):
        query = "SELECT * FROM ?;"
        args = (table_name,)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, args)
        data = cur.fetchall()
        cur.close()
        conn.commit()

        inv = UserInventory(discordid)
        for row in data:
            si = ship_stats.ShipInstance(row[0], row[1], discordid, row[2])
            inv.append(si)
        return inv
    else:
        # if user doesn't have an inventory, generate one from the base table
        sqlutils.copy_table(get_connection(), BASIC_TABLE_NAME, table_name)
        return get_user_inventory(discordid)
