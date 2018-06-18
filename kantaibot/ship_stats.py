"""Handles information about ships."""
import os
import userinfo
import json
import urllib
from io import BytesIO
from PIL import Image

DIR_PATH = os.path.dirname(os.path.realpath(__file__))

_json_cache = {}


def read_json(filepath):
    """Return the JSON inside of the given JSON file."""
    if (filepath in _json_cache):
        return _json_cache[filepath]
    with open(filepath, 'r', encoding='utf-8') as fileinfo:
        data = json.load(fileinfo)
        _json_cache[filepath] = data
        return data


SHIP_DATA_FILE = os.path.join(DIR_PATH, "../ships.json")
SHIP_DATA = read_json(SHIP_DATA_FILE)

_sbase_cache = {}


class ShipBase:
    """The base type of a ship, including its shared information."""

    def __init__(self, sid, data):
        """Initialize the ship base.

        Parameters
        ----------
        sid : int
            The ship ID of the ship
        data : dict
            The JSON data of the specified ship
        """
        self.sid = sid
        self.kc3id = data['kc3id']
        self.name = data['name']
        self.class_name = data['class_name']
        self.rarity = data['rarity']
        self.stype = data['stype']
        self.quotes = data['quotes']
        self.remodels_from = data['remodels_from']
        self.remodels_into = data['remodels_into']
        self.remodel_level = data['remodel_level']
        self.images = data['images']
        self.wiki_link = data['wiki_link']
        self.can_drop = data['can_drop']
        self.can_craft = data['can_craft']

    def instance(shipid):
        """Get an instance of ShipBase for the given ship id."""
        if (shipid in _sbase_cache):
            return _sbase_cache[shipid]

        data = SHIP_DATA[str(shipid)]
        ins = ShipBase(shipid, data)
        _sbase_cache[shipid] = ins
        return ins

    def get_quote(self, key):
        """Return a quote that the ship has, given its key."""
        if (key in self.quotes):
            return self.quotes[key]
        try:
            ship = self
            while (ship.remodels_from):
                ship = ShipBase.instance(ship.remodels_from)
                quo = ship.get_quote(key)
                if (quo):
                    return quo
        except TypeError:
            pass
        return "???"

    def get_first_base(self):
        """Get the original base of this ship, before all remodels."""
        ship = self
        try:
            while (ship.remodels_from):
                ship = ShipBase.instance(ship.remodels_from)
        except TypeError:
            pass
        return ship

    def get_cg(self, ico=False, dmg=False):
        """Return the full CG of the ship.

        Parameters
        ----------
        ico : bool
            True if requesting the icon, False if requesting the full CG.
        dmg : bool
            True if requesting the damaged version, False if normal version.

        Returns
        -------
        PIL.Image
            The CG requested, in its native size
        """
        file_dir = "../icos/" if ico else "../cgs/"
        file_dir = os.path.join(DIR_PATH, file_dir)
        info_name = 'small' if ico else 'full'
        info_name += '_damaged' if dmg else ''
        image_info = self.images[info_name]

        try:
            img = Image.open(file_dir + image_info['file_name'])
            return img
        except IOError:
            url = image_info['url']
            req = urllib.request.urlopen(url)
            imgdata = Image.open(BytesIO(req.read())).convert('RGBA')
            imgdata.save(file_dir + image_info['file_name'])
            return imgdata


class ShipInstance:
    """Represents an instance of a ship in a user's inventory."""

    def __init__(self, invid, sid, owner, level=1, exp=0):
        """Initialize the ship instance.

        Parameters
        ----------
        invid : int
            The inventory slot this ship takes up.
        sid : int
            The ship id of the ship.
        owner : int
            The discord id of the owner of this ship.
        level : int
            The ship's level.
        exp : int
            The ship's current exp.
        """
        self.invid = invid
        self.sid = sid
        self.owner = owner
        self.level = level
        self.exp = exp

    def base(self):
        """Return the ShipBase corresponding to this ship."""
        return ShipBase.instance(self.sid)

    def new(sid, owner):
        """Make a new ship with the given shipid owned by the given owner."""
        return ShipInstance(-1, sid, owner)

    def add_exp(self, exp):
        """Add EXP to the local copy of the ship.

        Returns
        -------
        bool
            Whether or not the ship levelled up in the process.
        """
        req = self.exp_req()
        self.exp += exp
        lvl = False
        if (self.level != 99 and self.level < 165):
            if (self.exp > req):
                self.level += 1
                self.exp -= req
                lvl = True
                self.add_exp(0)  # level up as much as possible
        else:
            self.exp = 0
        userinfo.update_ship_exp(self)
        return lvl

    def exp_req(self):
        """Get the amount of EXP required for the next level."""
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
            add = {91: 5, 92: 15, 93: 25, 94: 45, 95: 95, 96: 195, 97: 295,
                   98: 580}
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
                           160: 2000, 161: 2600, 162: 3300, 163: 4100,
                           164: 5000}
            if (self.level >= 155):
                base = upper_bases[self.level]
        return base * 100

    def is_remodel_ready(self):
        """Return true if the ship's level is high enough for a remodel."""
        base = self.base()
        if (not base.remodels_into):
            return False
        return self.level >= base.remodel_level


RARITY_COLORS = [(150, 150, 150), (150, 150, 150), (150, 150, 150),
                 (0, 122, 103), (255, 255, 50), (0, 255, 84),
                 (250, 25, 25), (255, 0, 234)]


def get_rarity_backdrop(rarity, size):
    """Return an image of the corresponding rarity background.

    Uses an 8-tiled image (Rarity_colors.jpg)

    Returns
    -------
    PIL.Image
        The image resized to the given size.
    """
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


ALL_SHIP_TYPES = []


class ShipType:
    """Type or class of a ship."""

    def __init__(self, discriminator, full_name, resource_mult=1.0):
        """Initialize the ship type.

        Parameters
        ----------
        discriminator : str
            The shorthand discriminator for the ship type.
        full_name : str
            The full type name.
        resource_mult : float
            A multiplier for the amount of resources this ship type takes
            compared to others.
        """
        self.discriminator = discriminator
        self.full_name = full_name
        self.resource_mult = resource_mult
        ALL_SHIP_TYPES.append(self)

    def __str__(self):
        """Return the full name of the ship."""
        return self.full_name


TYPE_DESTROYER = ShipType("DD", "Destroyer", resource_mult=0.5)
TYPE_LIGHT_CRUISER = ShipType("CL", "Light Cruiser", resource_mult=0.75)
TYPE_TORPEDO_CRUISER = ShipType("CLT", "Torpedo Cruiser", resource_mult=1.5)
TYPE_HEAVY_CRUISER = ShipType("CA", "Heavy Cruiser", resource_mult=1.5)
TYPE_AVIATION_CRUISER = ShipType("CAV", "Aviation Cruiser", resource_mult=1.5)
TYPE_BATTLESHIP = ShipType("BB", "Battleship", resource_mult=3.0)
TYPE_FAST_BATTLESHIP = ShipType("FBB", "Fast Battleship", resource_mult=3.0)
TYPE_AVIATION_BATTLESHIP = ShipType("BBV", "Aviation Battleship",
                                    resource_mult=3.0)
TYPE_LIGHT_CARRIER = ShipType("CVL", "Light Carrier", resource_mult=1.25)
TYPE_CARRIER = ShipType("CV", "Carrier", resource_mult=2)
TYPE_ARMORED_CARRIER = ShipType("CVB", "Armored Carrier", resource_mult=2.25)
TYPE_SEAPLANE_TENDER = ShipType("AV", "Seaplane Tender")
TYPE_SUBMARINE = ShipType("SS", "Submarine", resource_mult=0.4)
TYPE_AIRCRAFT_CARRYING_SUBMARINE = ShipType("SSV",
                                            "Aircraft Carrying Submarine",
                                            resource_mult=0.5)
TYPE_AMPHIBIOUS_ASSAULT_SHIP = ShipType("LHA", "Amphibious Assault Ship")
TYPE_REPAIR_SHIP = ShipType("AR", "Repair Ship")
TYPE_SUBMARINE_TENDER = ShipType("AS", "Submarine Tender", resource_mult=0.5)
TYPE_TRAINING_CRUISER = ShipType("CT", "Training Cruiser")
TYPE_FLEET_OILER = ShipType("AO", "Fleet Oiler")
TYPE_DESTROYER_ESCORT = ShipType("DE", "Coastal Defense Ship",
                                 resource_mult=0.5)


def get_ship_type(discrim):
    """Return the ShipType object corresponding to the given discriminator."""
    r = [x for x in ALL_SHIP_TYPES if x.discriminator == discrim]
    if len(r) > 0:
        return r[0]
    return None


def get_all_ships(allow_remodel=True, only_droppable=False,
                  only_craftable=False, type_discrims=None):
    """Return every ship base.

    Parameters
    ----------
    allow_remodel : bool
        If False, only return ships with no past remodels.
    only_droppable : bool
        If True, only return ships that are able to be dropped.
    only_craftable : bool
        If True, only return ships that can be crafted.
    type_discrims : list
        A list (str) of discriminators of ship types,
        if not None, only returns ships of the given types.
    """
    ret = []

    for sid in SHIP_DATA.keys():
        ins = ShipBase.instance(sid)
        if (only_droppable and not ins.can_drop):
            continue
        if (only_craftable and not ins.can_craft):
            continue
        if (ins.remodels_from and not allow_remodel):
            continue
        if (type_discrims and ins.stype not in type_discrims):
            continue
        ret.append(ins)

    return ret
