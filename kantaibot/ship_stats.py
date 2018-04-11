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

# Ship Type - The class of the ship
ALL_SHIP_TYPES = []
class ShipType:
    def __init__(self, tid, discriminator, full_name):
        self.tid = tid
        self.discriminator = discriminator
        self.full_name = full_name
        ALL_SHIP_TYPES.append(self)

TYPE_DESTROYER = ShipType(0, "DD", "Destroyer")
TYPE_LIGHT_CRUISER = ShipType(1, "CL", "Light Cruiser")
TYPE_HEAVY_CRUISER = ShipType(2, "CA", "Heavy Cruiser")
TYPE_LIGHT_CARRIER = ShipType(3, "CVL", "Light Carrier")
TYPE_CARRIER = ShipType(4, "CV", "Carrier")
TYPE_BATTLESHIP = ShipType(5, "BB", "Battleship")


# Ship Rarity - How rare the ship is to obtain randomly
ALL_SHIP_RARITIES = []
class ShipRarity:
    def __init__(self, rid, rarity_value, name):
        self.rid = rid
        self.rarity_value = rarity_value
        self.name = name
        ALL_SHIP_RARITIES.append(self)

RARITY_COMMON = ShipRarity(0, 100, "Common")
RARITY_UNCOMMON = ShipRarity(1, 75, "Uncommon")
RARITY_RARE = ShipRarity(2, 40, "Rare")
