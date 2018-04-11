import sys
sys.path.append("../kantaibot/")
import ship_stats
import sqlite3
import os
import htmlparsing
import json

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
DB_PATH = os.path.join(DIR_PATH, "../kantaidb.db")

HOME_DIR = os.path.expanduser("~")

def get_connection():
    return sqlite3.connect(DB_PATH)

ship_id = input("Ship ID: ")

# kc3 path
kc3_file_path = HOME_DIR + "/AppData/Local/Google/Chrome/User Data/Default/Extensions/hkgmldnainaglpjngpajnnjfhpdjkohh/32.4.4_0"
print("Searching KC3 stored information...")
db_path = "%s/data/WhoCallsTheFleet_ships.nedb" % (kc3_file_path)
db_data = []
with open(db_path, 'rb') as nedb:
    for line in map(lambda x: x.decode('utf-8'), nedb):
        data = json.loads(line)
        db_data.append(data)
kc3_id = 0
kc3_entry = None

def get_kc3_id(sid):
    for entry in db_data:
        if entry['no'] == int(sid):
            return entry['id']

def get_kc3_data(kcid):
    for entry in db_data:
        if entry['id'] == int(kcid):
            return entry

def get_ship_info(kcid, entry=None):
    if (not entry):
        entry = get_kc3_data(kcid)
    sname = entry['name']['ja_jp'] if len(entry['name']['ja_romaji']) == 0 else entry['name']['ja_romaji']
    sname = sname.title()
    tname = sname
    for o, t in ship_stats.SHIP_TRANSLATIONS.items():
        tname = tname.replace(o, t)
    stype = entry['type']
    srarity = entry['rare']
    suffix = 0
    if 'suffix' in entry['name'] and entry['name']['suffix']:
        suffix = ship_stats.SHIP_SUFFIXES[entry['name']['suffix']]
        sname += " " + suffix
        tname += " " + suffix
    return sname, tname, stype, srarity


kc3_id = get_kc3_id(ship_id)
kc3_entry = get_kc3_data(kc3_id)
ship_name, translated_name, ship_type, ship_rarity = get_ship_info(kc3_id, kc3_entry)
if (kc3_id == 0):
    print("ID not found")
    input()
    exit()
type_discrim = ship_stats.get_ship_type(ship_type).discriminator
print("Found ship '%s' of type %s and rarity %s with KC3 ID %s" % (ship_name, type_discrim, ship_rarity, kc3_id))
img_small_path = "%s/assets/img/ships/%s.png" % (kc3_file_path, kc3_id)
img_small_damaged_path = "%s/assets/img/ships/%s_d.png" % (kc3_file_path, kc3_id)

# kcwiki data
def perform_search(tname, stype, kcid):
    print("Fetching images from Kancolle Wiki...")
    typeobj = ship_stats.get_ship_type(stype)
    imgs = htmlparsing.get_images_on_wiki_page(tname)
    img_name_reg = "%s %s %03d Full" % (typeobj.discriminator, tname, int(kcid))
    img_name_dmg = "%s Damaged" % (img_name_reg)
    print("Searching for images: " + str([img_name_reg, img_name_dmg]))
    try:
        img_reg = [y for x, y in imgs.items() if x == img_name_reg].pop()
        img_dmg = [y for x, y in imgs.items() if x == img_name_dmg].pop()
        print("Found images: " + str([img_reg, img_dmg]))
    except IndexError:
        img_reg = None
        img_dmg = None
    return img_reg, img_dmg
img_reg, img_dmg = perform_search(translated_name, ship_type, kc3_id)
if (not img_reg or not img_dmg):
    print("One or more images not found")
    if ('prev' in kc3_entry['remodel']):
        prev_id = kc3_entry['remodel']['prev']
        print("Checking previous remodel...")
        pname, ptname, ptype, prarity = get_ship_info(prev_id)
        img_reg, img_dmg = perform_search(ptname, ptype, prev_id)
        if (not img_reg or not img_dmg):
            print("!! Could not find missing images")

query = "REPLACE INTO ShipBase (ShipID, Name, Rarity, ShipType, Image_Default, Image_Damaged, Image_Small, Image_Small_Damaged) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');"
query = query % (ship_id, ship_name, ship_rarity, ship_type, img_reg, img_dmg, img_small_path, img_small_damaged_path)
conn = get_connection()
cur = conn.cursor()
cur.execute(query)
cur.close()
conn.commit()

print("Added to database")
input() # stops command prompt auto closing
