# file for storing classes related to stats and misc information about ships

# Base class for a certain ship, as in database
class ShipBase:
    def __init__(self, sid, name, rarity, shiptype, imagedef):
        self.sid = sid
        self.name = name
        self.rarity = rarity
        self.shiptype = shiptype
        self.imagedef = imagedef

# Instance of a ship, existing in a user's inventory
class ShipInstance:
    def __init__(self, invid, sid, level=1):
        self.invid = invid
        self.sid = sid
        self.level = level

    def new(sid):
        return ShipInstance(-1, sid)

# Suffixes at the end of a ship's name, using KC3 values

SHIP_SUFFIXES = {0: "", 1: "Kai", 2: "Kai Ni", 3: "A", 4: "Carrier",
                 5: "Carrier Kai", 6: "Carrier Kai Ni", 7: "zwei",
                 8: "drei", 9: "Kai Ni A", 10: "Kai Ni B",
                 11: "Kai Ni B", 12: "due", 13: "Kai Bo", 14: "dva",
                 15: "Mk.II", 16: "Mk.II Mod.2", 17: "B Kai"}

# Translations for Russian ships as KC3 does not store the english name

SHIP_TRANSLATIONS = {u"Гангут": "Gangut", u"Верный": "Verniy",
                     u"Октябрьская революция": "Oktyabrskaya Revolyutsiya",
                     u"Ташкент": "Tashkent"}

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
