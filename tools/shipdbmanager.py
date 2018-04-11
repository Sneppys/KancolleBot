import sys
sys.path.append("../kantaibot/")
import ship_stats
import sqlite3
import os

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
DB_PATH = os.path.join(DIR_PATH, "../kantaidb.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

ship_id = input("Ship ID: ")
ship_name = input("Ship Name: ")
for type in ship_stats.ALL_SHIP_TYPES:
    print(type.tid, type.discriminator)
ship_type = input("Ship Type (id): ")
for rarity in ship_stats.ALL_SHIP_RARITIES:
    print(rarity.rid, rarity.name)
ship_rarity = input("Ship Rarity (id): ")
img_path1 = input("Ship Image (base): ")

query = "REPLACE INTO ShipBase (ShipID, Name, Rarity, ShipType, Image_Default) VALUES ('%s', '%s', '%s', '%s', '%s');"
query = query % (ship_id, ship_name, ship_rarity, ship_type, img_path1)
conn = get_connection()
cur = conn.cursor()
cur.execute(query)
cur.close()
conn.commit()

print("Added to database")
input() # stops command prompt auto closing
