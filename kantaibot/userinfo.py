import sqlite3
import os
import ship_stats
import sqlutils

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
DB_PATH = os.path.join(DIR_PATH, "../usersdb.db") # hidden to git

USER_TABLE_NAME = "INV_%s"
BASIC_TABLE_NAME = "INV_BASIC"

class User:
    def __init__(self, did):
        self.did = did

class UserInventory:
    def __init__(self, did):
        self.did = did
        self.inventory = []

    def append(self, ship_instance):
        self.inventory.append(ship_instance)

    def add_to_inventory(self, ship_instance):
        table_name = USER_TABLE_NAME % (self.did)
        query = "INSERT INTO %s (ShipID) VALUES (%s);" % (table_name, ship_instance.sid)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query)
        cur.close()
        conn.commit()

    def remove_from_inventory(self, inv_id):
        table_name = USER_TABLE_NAME % (self.did)
        query = "DELETE FROM %s WHERE ID='%s';" % (table_name, inv_id)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query)
        cur.close()
        conn.commit()

def get_connection():
    return sqlite3.connect(DB_PATH)

def get_user(discordid):
    query = "SELECT * FROM Users WHERE DiscordID=%s;" % (discordid)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query)
    data = cur.fetchall()
    cur.close()
    conn.commit()

    if (len(data) == 0):
        # if user doesn't exist, create it
        query = "REPLACE INTO Users (DiscordID) VALUES (%s);" % discordid
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query)
        cur.close()
        conn.commit()
        return get_user(discordid)
    row = data[0]
    return User(row[0])

def get_user_inventory(discordid):
    table_name = USER_TABLE_NAME % discordid
    if (sqlutils.table_exists(get_connection(), table_name)):
        query = "SELECT * FROM %s;" % table_name
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query)
        data = cur.fetchall()
        cur.close()
        conn.commit()

        inv = UserInventory(discordid)
        for row in data:
            si = ship_stats.ShipInstance(row[0], row[1], row[2])
            inv.append(si)
        return inv
    else:
        # if user doesn't have an inventory, generate one from the base table
        sqlutils.copy_table(get_connection(), BASIC_TABLE_NAME, table_name)
        return get_user_inventory(discordid)
