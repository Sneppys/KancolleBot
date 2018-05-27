"""Handles information about ships."""
import os
import userinfo
import json
import htmlparsing
import urllib
from io import BytesIO
from PIL import Image

DIR_PATH = os.path.dirname(os.path.realpath(__file__))

# HOME_DIR = os.path.expanduser("~")
with open(os.path.join(DIR_PATH, 'botinfo.json'), 'r') as bi:
    info = json.load(bi)
    HOME_DIR = info['home_dir']
kc3_file_path = HOME_DIR + ("/AppData/Local/Google/Chrome/"
                            "User Data/Default/Extensions/"
                            "hkgmldnainaglpjngpajnnjfhpdjkohh/")
# get current version
ver_dir = next(filter(os.path.isdir, [os.path.join(kc3_file_path, f)
                                      for f in os.listdir(kc3_file_path)]))
kc3_file_path = ver_dir

LOCALIZED_DIR = os.path.join(kc3_file_path, "data/lang/data/en/")
DATA_DIR = os.path.join(kc3_file_path, "data/")

MASTER_DATA = os.path.join(DIR_PATH, "../data.json")

WHOCALLSTHEFLEET_DB = DATA_DIR + "WhoCallsTheFleet_ships.nedb"

_json_cache = {}
_wctf_cache = None


def get_row(condition):
    """Return the first JSON row of the WCTF database matching a function."""
    global _wctf_cache
    if(not _wctf_cache):
        with open(WHOCALLSTHEFLEET_DB, 'r', encoding='utf-8') as nedb:
            _wctf_cache = [json.loads(x) for x in nedb]
    row_gen = (x for x in _wctf_cache)
    return next(x for x in row_gen if condition(x))


def get_kc3_id(shipid):
    """Convert a ship id to the corresponding kc3 id."""
    return get_row(lambda l: l['no'] == shipid)['id']


def get_ship_id(kc3id):
    """Convert a kc3 id to the corresponding ship id."""
    return get_row(lambda l: l['id'] == kc3id)['no']


def read_json(filepath):
    """Return the JSON inside of the given JSON file."""
    if (filepath in _json_cache):
        return _json_cache[filepath]
    with open(filepath, 'r', encoding='utf-8') as fileinfo:
        data = json.load(fileinfo)
        _json_cache[filepath] = data
        return data


def read_localized(filename):
    """Return the JSON of the kc3 localization file."""
    return read_json(LOCALIZED_DIR + filename)


def read_data(filename):
    """Return the JSON of a kc3 data file."""
    return read_json(DATA_DIR + filename)


def get_master_entry(shipid):
    """Get the JSON entry in the local ship data file of the specified ship."""
    data = read_json(MASTER_DATA)
    kc3id = get_kc3_id(shipid)
    return data['ship'][str(kc3id)]


_sbase_cache = {}
_imgurl_cache = {}


class ShipBase:
    """The base type of a ship, including its shared information."""

    def __init__(self, sid, kc3id, name, class_name, rarity, stype, quotes,
                 remodels_from, remodels_into, remodel_level):
        """Initialize the ship base.

        Parameters
        ----------
        sid : int
            The ship id of the ship.
        kc3id : int
            The kc3 id of the ship.
        name : str
            The english name of the ship.
        class_name : str
            The english name of the ship's class.
        rarity : int
            An integer, 1-8 inclusive, of the ship's rarity.
        stype : str
            The discriminator for the ship's type.
        quotes : dict
            The JSON data of the quotes of this ships.
        remodels_from : int
            The ship id of the previous remodel, None if none exists.
        remodels_into : int
            The ship id of the ship this remodels into, None of none exists.
        remodel_level : int
            The level this ship needs to remodel into the next ship.
        """
        self.sid = sid
        self.kc3id = kc3id
        self.name = name
        self.class_name = class_name
        self.rarity = rarity
        self.stype = stype
        self._quotes = quotes
        self.remodels_from = remodels_from
        self.remodels_into = remodels_into
        self.remodel_level = remodel_level

    def instance(shipid):
        """Get an instance of ShipBase for the given ship id."""
        if (shipid in _sbase_cache):
            return _sbase_cache[shipid]

        data = get_row(lambda l: l['no'] == shipid)
        master = get_master_entry(shipid)

        kc3id = data['id']

        # localization
        name = master['api_name']
        locdata = read_localized('ships.json')
        for jp in sorted(locdata, key=lambda x: -len(x)):
            en = locdata[jp]
            name = name.replace(jp, en)
        affix = read_localized('ship_affix.json')
        for jp in sorted(affix['suffixes'], key=lambda x: -len(x)):
            en = affix['suffixes'][jp]
            name = name.replace(jp, en)
        class_data = read_localized('ctype.json')
        class_jp = class_data[master['api_ctype']]
        for jp in sorted(locdata, key=lambda x: -len(x)):
            en = locdata[jp]
            class_jp = class_jp.replace(jp, en)
        for jp in sorted(affix['ctype'], key=lambda x: -len(x)):
            en = affix['ctype'][jp]
            class_jp = class_jp.replace(jp, en)
        if (class_jp == "Amphibious Assault Ship"):
            # Amphibious Assault Ship Amphibious Assault Ship
            class_jp = "Hei Class"

        quotedata = read_localized('quotes.json')
        if (str(kc3id) in quotedata):
            quotes = quotedata[str(kc3id)]
        else:
            quotes = []

        rarity = int(data['rare'])
        stype = master['api_stype']
        stype_data = read_localized('stype.json')
        stype_discrim = stype_data[stype]

        r_into = None
        r_from = None
        r_level = None
        if ('remodel' in data):
            rmdl = data['remodel']
            if ('next' in rmdl):
                r_into = get_ship_id(rmdl['next'])
                r_level = rmdl['next_lvl']
            if ('prev' in rmdl):
                r_from = get_ship_id(rmdl['prev'])

        ins = ShipBase(shipid, kc3id, name, class_jp, rarity, stype_discrim,
                       quotes, r_from, r_into, r_level)
        _sbase_cache[shipid] = ins
        return ins

    def get_quote(self, key):
        """Return a quote that the ship has, given its key."""
        if (key in self._quotes):
            e = self._quotes[key]
            if (type(e) is dict):
                e = " ".join(list(e[x] for x in sorted(e)))
            e = e.replace("<br />", " ")
            return e
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

    # image management

    def get_wiki_link(self):
        """Get the URL of the kancolle wiki page of this ship."""
        base = self.get_first_base()
        url = "http://kancolle.wikia.com/wiki/%s" % (
            base.name.replace(' ', '_').replace('.', '._'))  # fucking sammy b
        return url

    def get_image_urls(self):
        """Get all the images in the wiki page for the ship.

        Returns
        -------
        dict
            A dictionary, key being the name of the image, value being its URL.
        """
        wiki = self.get_wiki_link()
        if (wiki in _imgurl_cache):
            return _imgurl_cache[wiki]
        imgs = htmlparsing.get_images_on_wiki_page(wiki)
        _imgurl_cache[wiki] = imgs
        return imgs

    def get_remote_img_names(self):
        """Get the name of the images of this ship's CG art.

        Returns
        -------
        tuple
            A 2-tuple of the ship's normal cg name, and the damaged version.
        """
        name = self.name
        if (self.sid in _IMG_EXCLUSIONS):
            name = _IMG_EXCLUSIONS[self.sid]
        if ('-Kou' in name):
            name = name.replace('-Kou', ' Carrier')
        n = "%s %s %03d Full" % (self.stype, name, self.kc3id)
        d = n + " Damaged"
        return (n, d)

    def get_main_cg(self):
        """Return the URL of both cgs of the ship.

        Returns
        -------
        tuple
            A 2-tuple of the URLs of the images, normal then damaged
        """
        norm = ""
        dmg = ""
        img_urls = self.get_image_urls()
        names = list(self.get_remote_img_names())
        base = self
        found = False
        while (not found):
            for k, v in img_urls.items():
                if (k.lower() == names[0].lower()):
                    norm = v
                    found = True
                    break
            if (not base.remodels_from):
                break
            base = ShipBase.instance(base.remodels_from)
            names[0] = base.get_remote_img_names()[0]
        base = self
        found = False
        while (not found):
            for k, v in img_urls.items():
                if (k.lower() == names[1].lower()):
                    dmg = v
                    found = True
                    break
            if (not base.remodels_from):
                break
            base = ShipBase.instance(base.remodels_from)
            names[1] = base.get_remote_img_names()[1]
        return (norm, dmg)

    def get_ico_path(self):
        """Return the local kc3 icons for the normal and damaged states."""
        ico_n = os.path.join(kc3_file_path,
                             './assets/img/ships/%s.png' % (self.kc3id))
        ico_d = os.path.join(kc3_file_path,
                             './assets/img/ships/%s_d.png' % (self.kc3id))
        return (ico_n, ico_d)

    def get_local_paths(self):
        """Return the local path for the full cgs, normal and damaged."""
        path_b = '../cgs/%s.png'
        path_n = os.path.join(DIR_PATH, path_b % (str(self.sid)))
        path_d = os.path.join(DIR_PATH, path_b % (str(self.sid) + "_d"))
        return (path_n, path_d)

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
        if (ico):
            return Image.open(self.get_ico_path()[1 if dmg else 0])
        else:
            path = self.get_local_paths()[1 if dmg else 0]
            try:
                img = Image.open(path).convert('RGBA')
                return img
            except (IOError, FileNotFoundError) as e:
                url = self.get_main_cg()[1 if dmg else 0]
                req = urllib.request.urlopen(url)
                imgdata = Image.open(BytesIO(req.read())).convert('RGBA')
                imgdata.save(path)
                return imgdata


# Weird image naming inconsistencies
_IMG_EXCLUSIONS = {147: 'Верный', 361: 'Samuel B. Roberts',
                   321: 'Kasuga Maru', 161: 'Akitsu Maru'}


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

    exclusions = read_json(os.path.join(DIR_PATH, 'drop_exclusions.json'))
    data = read_json(MASTER_DATA)
    for k, v in data['ship'].items():
        if ('api_sortno' in v):
            sid = v['api_sortno']
            if (only_droppable and sid in exclusions['drops']):
                continue
            if (only_craftable and sid in exclusions['crafting']):
                continue
            ins = ShipBase.instance(sid)
            if (ins.remodels_from and not allow_remodel):
                continue
            if (type_discrims and ins.stype not in type_discrims):
                continue
            ret.append(ins)

    return ret
