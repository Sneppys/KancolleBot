import sqlite3
import os
import ship_stats
import sqlutils
import userinfo
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
        query = "SELECT ShipID, Name, Rarity, ShipType, Remodels_From, Remodels_Into, Remodel_Level FROM ShipBase WHERE ShipID=?"
        args = (shipid,)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, args)
        data = cur.fetchone()
        cur.close()
        conn.commit()
        return ShipBase(data[0], data[1], data[2], data[3], data[4], data[5], data[6])

    # track all remodel from until first version reached
    def get_first_base(self):
        ship = self
        try:
            while (ship.remodels_from):
                ship = ShipBase.instance(ship.remodels_from)
        except TypeError:
            pass
        return ship

# Instance of a ship, existing in a user's inventory
class ShipInstance:
    def __init__(self, invid, sid, owner, level=1, exp=0):
        self.invid = invid
        self.sid = sid
        self.owner = owner
        self.level = level
        self.exp = exp

    def base(self):
        return ShipBase.instance(self.sid)

    def new(sid, owner):
        return ShipInstance(-1, sid, owner)

    # add exp to ship instance, returns True for level up
    def add_exp(self, exp):
        req = self.exp_req()
        self.exp += exp
        lvl = False
        if (self.level != 99 and self.level < 165):
            if (self.exp > req):
                self.level += 1
                self.exp -= req
                lvl = True
                self.add_exp(0) # level up as much as possible
        else:
            self.exp = 0
        userinfo.update_ship_exp(self)
        return lvl

    def exp_req(self):
        if (self.level < 99):
            base = self.level
            if (self.level > 50):
                base += self.level - 50
            if (self.level > 60):
                base += self.level - 60
            if (self.level > 70):
                base += self.level - 70
            if (self.level > 80):
                base += self.level - 80
            add = {91: 5, 92: 15, 93: 25, 94: 45, 95: 95, 96: 195, 97: 295, 98: 580}
            for a, v in add.items():
                if (self.level >= a):
                    base += v
        elif (self.level == 99 or self.level >= 165):
            return 0
        else:
            base = self.level
            lvl = self.level - 100
            if (self.level > 100):
                base -= 100
                base += lvl * 9
            if (self.level > 110):
                base += (lvl - 10) * 10
            if (self.level > 115):
                base += (lvl - 15) * 10
            if (self.level > 120):
                base += (lvl - 20) * 10
            if (self.level > 130):
                base += (lvl - 30) * 10
            if (self.level >= 140):
                base += (lvl - 39) * 20
            if (self.level >= 145):
                base += (lvl - 44) * 10
            if (self.level >= 150):
                base += (lvl - 49) * 10
            upper_bases = {155: 2500, 156: 600, 157: 800, 158: 1100, 159: 1500,
                           160: 2000, 161: 2600, 162: 3300, 163: 4100, 164: 5000}
            if (self.level >= 155):
                base = upper_bases[self.level]
        return base * 100

    def is_remodel_ready(self):
        base = self.base()
        if (not base.remodels_into):
            return False
        return self.level >= base.remodel_level

# Suffixes at the end of a ship's name, using KC3 values

SHIP_SUFFIXES = {0: "", 1: "Kai", 2: "Kai Ni", 3: "A", 4: "Carrier",
                 5: "Carrier Kai", 6: "Carrier Kai Ni", 7: "zwei",
                 8: "drei", 9: "Kai Ni A", 10: "Kai Ni B",
                 11: "Kai Ni D", 12: "due", 13: "Kai Bo", 14: "два",
                 15: "Mk.II", 16: "Mk.II Mod.2", 17: "B Kai"}

# What the fuck, KC3? (Maps KC3's internal 'remodel level' to the actual value)

REAL_REMODEL_LEVEL = { 1: 80, 3: 77, 5: 20, 7: 84, 8: 90, 10: 50,
                     12: 10, 16: 12, 20: 25, 21: 78, 24: 85, 25: 89,
                     68: 15, 36: 30, 47: 55, 51: 70, 53: 60, 56: 63,
                     58: 65, 60: 67, 61: 68, 65: 75, 72: 35, 74: 37,
                     77: 40, 82: 45, 84: 47, 89: 48, 91: 19, 92: 18,
                     103: 88}

# Translations for Russian ships as KC3 does not store the english name

SHIP_TRANSLATIONS = {u"Гангут": "Gangut", u"Верный": "Verniy",
                     u"Октябрьская революция": "Oktyabrskaya Revolyutsiya",
                     u"Ташкент": "Tashkent", u"два": "dva", u"伊": "I-"}

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
    def __init__(self, tid, discriminator, full_name, resource_mult=1.0, alt_ids=[]):
        self.tid = tid
        self.discriminator = discriminator
        self.full_name = full_name
        self.resource_mult = resource_mult
        self.alt_ids = alt_ids
        ALL_SHIP_TYPES.append(self)

TYPE_DESTROYER = ShipType(1, "DD", "Destroyer", resource_mult=0.5, alt_ids=[19])
TYPE_LIGHT_CRUISER = ShipType(2, "CL", "Light Cruiser", resource_mult=0.75, alt_ids=[28])
TYPE_TORPEDO_CRUISER = ShipType(3, "CLT", "Torpedo Cruiser", resource_mult=1.5)
TYPE_HEAVY_CRUISER = ShipType(4, "CA", "Heavy Cruiser", resource_mult=1.5, alt_ids=[23])
TYPE_AVIATION_CRUISER = ShipType(5, "CAV", "Aviation Cruiser", resource_mult=1.5)
TYPE_BATTLESHIP = ShipType(6, "BB", "Battleship", resource_mult=3.0)
TYPE_FAST_BATTLESHIP = ShipType(7, "FBB", "Fast Battleship", resource_mult=3.0)
TYPE_AVIATION_BATTLESHIP = ShipType(8, "BBV", "Aviation Battleship", resource_mult=3.0)
TYPE_LIGHT_CARRIER = ShipType(9, "CVL", "Light Carrier", resource_mult=1.25, alt_ids=[32])
TYPE_CARRIER = ShipType(10, "CV", "Carrier", resource_mult=2)
TYPE_ARMORED_CARRIER = ShipType(11, "CVB", "Armored Carrier", resource_mult=2.25)
TYPE_SEAPLANE_TENDER = ShipType(12, "AV", "Seaplane Tender", alt_ids=[24])
TYPE_SUBMARINE = ShipType(13, "SS", "Submarine", resource_mult=0.4)
TYPE_AIRCRAFT_CARRYING_SUBMARINE = ShipType(14, "SSV", "Aircraft Carrying Submarine", resource_mult=0.5)
TYPE_AMPHIBIOUS_ASSAULT_SHIP = ShipType(15, "LHA", "Amphibious Assault Ship")
TYPE_REPAIR_SHIP = ShipType(16, "AR", "Repair Ship")
TYPE_SUBMARINE_TENDER = ShipType(17, "AS", "Submarine Tender", resource_mult=0.5)
TYPE_TRAINING_CRUISER = ShipType(21, "CT", "Training Cruiser")
TYPE_FLEET_OILER = ShipType(29, "AO", "Fleet Oiler")
TYPE_DESTROYER_ESCORT = ShipType(31, "DE", "Coastal Defense Ship", resource_mult=0.5)

def get_ship_type(tid):
    r = [x for x in ALL_SHIP_TYPES if x.tid == int(tid) or int(tid) in x.alt_ids]
    if len(r) > 0:
        return r[0]
    return None

def get_all_ships(cur=None, allow_remodel=True, only_droppable=False, only_craftable=False, type_ids=None):
    args = ()
    if (allow_remodel):
        query = "SELECT (ShipID) FROM ShipBase"
        if (type_ids):
            type_string = "(%s)" % (", ".join(map(str, type_ids)))
            query += "WHERE ShipType IN %s" % type_string
    else:
        query = "SELECT (ShipID) FROM ShipBase WHERE Remodels_From == 'None'"
        if (type_ids):
            type_string = "(%s)" % (", ".join(map(str, type_ids)))
            query += "AND ShipType IN %s" % type_string
        if (only_droppable):
            query += "AND Can_Drop='1'"
        if (only_craftable):
            query += "AND Can_Craft='1'"
    autoclose = False
    if not cur:
        conn = get_connection()
        cur = conn.cursor()
        autoclose = True
    cur.execute(query, args)
    ret = []
    for row in cur.fetchall():
        ret.append(ShipBase.instance(row[0]))
    if (autoclose):
        cur.close()
        conn.commit()

    return ret
