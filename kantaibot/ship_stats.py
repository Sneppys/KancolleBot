import sqlite3
import os
import ship_stats
import sqlutils
from PIL import Image

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
DB_PATH = os.path.join(DIR_PATH, "../kantaidb.db") # hidden to git

def get_connection():
    return sqlite3.connect(DB_PATH)

# file for storing classes related to stats and misc information about ships

# Base class for a certain ship, as in database
class ShipBase:
    def __init__(self, sid, name, rarity, shiptype, remodels_from, remodels_into, remodel_level):
        self.sid = sid
        self.name = name
        self.rarity = rarity
        self.shiptype = shiptype
        self.remodels_from = remodels_from
        self.remodels_into = remodels_into
        self.remodel_level = remodel_level

    def instance(shipid):
        query = "SELECT ShipID, Name, Rarity, ShipType, Remodels_From, Remodels_Into, Remodel_Level FROM ShipBase WHERE ShipID='%s';" % shipid
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query)
        data = cur.fetchall()[0]
        cur.close()
        conn.commit()
        return ShipBase(data[0], data[1], data[2], data[3], data[4], data[5], data[6])

# Instance of a ship, existing in a user's inventory
class ShipInstance:
    def __init__(self, invid, sid, owner, level=1):
        self.invid = invid
        self.sid = sid
        self.owner = owner
        self.level = level

    def base(self):
        return ShipBase.instance(self.sid)

    def new(sid, owner):
        return ShipInstance(-1, sid, owner)

# Suffixes at the end of a ship's name, using KC3 values

SHIP_SUFFIXES = {0: "", 1: "Kai", 2: "Kai Ni", 3: "A", 4: "Carrier",
                 5: "Carrier Kai", 6: "Carrier Kai Ni", 7: "zwei",
                 8: "drei", 9: "Kai Ni A", 10: "Kai Ni B",
                 11: "Kai Ni D", 12: "due", 13: "Kai Bo", 14: "два",
                 15: "Mk.II", 16: "Mk.II Mod.2", 17: "B Kai"}

# Translations for Russian ships as KC3 does not store the english name

SHIP_TRANSLATIONS = {u"Гангут": "Gangut", u"Верный": "Verniy",
                     u"Октябрьская революция": "Oktyabrskaya Revolyutsiya",
                     u"Ташкент": "Tashkent", u"два": "dva"}

# uses Rarity_colors.jpg to get a backdrop for different rarities

RARITY_COLORS = [(150, 150, 150), (150, 150, 150), (150, 150, 150),
                 (0, 122, 103), (255, 255, 50), (0, 255, 84),
                 (250, 25, 25), (255, 0, 234)]

def get_rarity_backdrop(rarity, size):
    rarity -= 1
    rimg = Image.open(DIR_PATH + '/Rarity_colors.jpg')
    w, h = rimg.size
    start_x = int(rarity % 4 * (w / 4)) + 10
    start_y = int(rarity // 4 * (h / 2)) + 15
    max_w = int(w / 4) - 20
    max_h = int(h / 2) - 30
    if (w > h):
        targ_w = max_w
        targ_h = (h / w) * targ_w
    else:
        targ_h = max_h
        targ_w = (w / h) * targ_h
    if (targ_h > max_h):
        targ_h = max_h
    if (targ_w > max_w):
        targ_w = max_w
    targ_w = int(targ_w)
    targ_h = int(targ_h)
    rimg = rimg.crop((start_x, start_y, start_x + targ_w, start_y + targ_h))
    rimg = rimg.resize(size, resample=Image.BICUBIC)
    return rimg

# Ship Type - The type of the ship, using KC3's internal type ids (Sometimes dupes)
ALL_SHIP_TYPES = []
class ShipType:
    def __init__(self, tid, discriminator, full_name):
        self.tid = tid
        self.discriminator = discriminator
        self.full_name = full_name
        ALL_SHIP_TYPES.append(self)

TYPE_DESTROYER = ShipType(1, "DD", "Destroyer")
TYPE_LIGHT_CRUISER = ShipType(2, "CL", "Light Cruiser")
TYPE_TORPEDO_CRUISER = ShipType(3, "CLT", "Torpedo Cruiser")
TYPE_HEAVY_CRUISER = ShipType(4, "CA", "Heavy Cruiser")
TYPE_AVIATION_CRUISER = ShipType(5, "CAV", "Aviation Cruiser")
TYPE_BATTLESHIP = ShipType(6, "BB", "Battleship")
TYPE_FAST_BATTLESHIP = ShipType(7, "FBB", "Fast Battleship")
TYPE_AVIATION_BATTLESHIP = ShipType(8, "BBV", "Aviation Battleship")
TYPE_LIGHT_CARRIER = ShipType(9, "CVL", "Light Carrier")
TYPE_CARRIER = ShipType(10, "CV", "Carrier")
TYPE_ARMORED_CARRIER = ShipType(11, "CVB", "Armored Carrier")
TYPE_SEAPLANE_TENDER = ShipType(12, "AV", "Seaplane Tender")
TYPE_SUBMARINE = ShipType(13, "SS", "Submarine")
TYPE_SUBMARINE_ALT = ShipType(14, "SS", "Submarine")
TYPE_AMPHIBIOUS_ASSAULT_SHIP = ShipType(15, "LHA", "Amphibious Assault Ship")
TYPE_REPAIR_SHIP = ShipType(16, "AR", "Repair Ship")
TYPE_SUBMARINE_TENDER = ShipType(17, "AS", "Submarine Tender")
TYPE_DESTROYER_ALT = ShipType(19, "DD", "Destroyer")
TYPE_TRAINING_CRUISER = ShipType(21, "CT", "Training Cruiser")
TYPE_HEAVY_CRUISER_ALT = ShipType(23, "CA", "Heavy Cruiser")
TYPE_SEAPLANE_TENDER_ALT = ShipType(24, "AV", "Seaplane Tender")
TYPE_LIGHT_CRUISER_ALT = ShipType(28, "CL", "Light Cruiser")
TYPE_FLEET_OILER = ShipType(29, "AO", "Fleet Oiler")
TYPE_DESTROYER_ESCORT = ShipType(31, "DE", "Coastal Defense Ship")
TYPE_LIGHT_CARRIER_ALT = ShipType(32, "CVL", "Light Carrier")

def get_ship_type(tid):
    r = [x for x in ALL_SHIP_TYPES if x.tid == int(tid)]
    if len(r) > 0:
        return r[0]
    return None


def get_all_ships(allow_remodel=True):
    if (allow_remodel):
        query = "SELECT (ShipID) FROM ShipBase;"
    else:
        query = "SELECT (ShipID) FROM ShipBase WHERE Remodels_From == 'None';"
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query)
    ids = cur.fetchall()
    cur.close()
    conn.commit()

    return [ShipBase.instance(id) for id in ids]
