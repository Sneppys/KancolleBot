import sqlite3
import os
import ship_stats
import sqlutils
import userinfo
import json
import htmlparsing
import urllib
from io import BytesIO
from PIL import Image

DIR_PATH = os.path.dirname(os.path.realpath(__file__))

#HOME_DIR = os.path.expanduser("~")
with open(os.path.join(DIR_PATH, 'botinfo.json'), 'r') as bi:
    info = json.load(bi)
    HOME_DIR = info['home_dir']
kc3_file_path = HOME_DIR + "/AppData/Local/Google/Chrome/User Data/Default/Extensions/hkgmldnainaglpjngpajnnjfhpdjkohh/"
ver_dir = next(filter(os.path.isdir, [os.path.join(kc3_file_path, f) for f in os.listdir(kc3_file_path)])) # get current version
kc3_file_path = ver_dir

LOCALIZED_DIR = os.path.join(kc3_file_path, "data/lang/data/en/")
DATA_DIR = os.path.join(kc3_file_path, "data/")

MASTER_DATA = os.path.join(DIR_PATH, "../data.json")

WHOCALLSTHEFLEET_DB = DATA_DIR + "WhoCallsTheFleet_ships.nedb"

_json_cache = {}
_wctf_cache = None

def get_row(condition):
    global _wctf_cache
    if(not _wctf_cache):
        with open(WHOCALLSTHEFLEET_DB, 'r', encoding='utf-8') as nedb:
            _wctf_cache = [json.loads(x) for x in nedb]
    row_gen = (x for x in _wctf_cache)
    return next(x for x in row_gen if condition(x))

def get_kc3_id(shipid):
    return get_row(lambda l: l['no'] == shipid)['id']

def get_ship_id(kc3id):
    return get_row(lambda l: l['id'] == kc3id)['no']

def read_json(filepath):
    if (filepath in _json_cache):
        return _json_cache[filepath]
    with open(filepath, 'r', encoding='utf-8') as fileinfo:
        data = json.load(fileinfo)
        _json_cache[filepath] = data
        return data

def read_localized(filename):
    return read_json(LOCALIZED_DIR + filename)

def read_data(filename):
    return read_json(DATA_DIR + filename)

def get_master_entry(shipid):
    data = read_json(MASTER_DATA)
    kc3id = get_kc3_id(shipid)
    return data['ship'][str(kc3id)]

_sbase_cache = {}
_imgurl_cache = {}

# Base class for a certain ship, as in database
class ShipBase:
    def __init__(self, sid, kc3id, name, class_name, rarity, stype, quotes, remodels_from, remodels_into, remodel_level):
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
            class_jp = "Hei Class" # Amphibious Assault Ship Amphibious Assault Ship

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

        ins = ShipBase(shipid, kc3id, name, class_jp, rarity, stype_discrim, quotes, r_from, r_into, r_level)
        _sbase_cache[shipid] = ins
        return ins

    def get_quote(self, key):
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

    # track all remodel from until first version reached
    def get_first_base(self):
        ship = self
        try:
            while (ship.remodels_from):
                ship = ShipBase.instance(ship.remodels_from)
        except TypeError:
            pass
        return ship

    # image management

    def get_wiki_link(self):
        base = self.get_first_base()
        row = get_row(lambda x: x['no'] == base.sid)
        url = "http://kancolle.wikia.com/wiki/%s" % (base.name.replace(' ', '_').replace('.', '._')) # fucking sammy b
        return url

    def get_image_urls(self):
        wiki = self.get_wiki_link()
        if (wiki in _imgurl_cache):
            return _imgurl_cache[wiki]
        imgs = htmlparsing.get_images_on_wiki_page(wiki)
        _imgurl_cache[wiki] = imgs
        return imgs

    def get_remote_img_names(self):
        name = self.name
        if (self.sid in _IMG_EXCLUSIONS):
            name = _IMG_EXCLUSIONS[self.sid]
        n = "%s %s %03d Full" % (self.stype, name, self.kc3id)
        d = n + " Damaged"
        return (n, d)

    def get_main_cg(self):
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
            names[0] = base.get_remote_img_names()[1]
        return (norm, dmg)

    def get_ico_path(self):
        ico_n = os.path.join(kc3_file_path, './assets/img/ships/%s.png' % (self.kc3id))
        ico_d = os.path.join(kc3_file_path, './assets/img/ships/%s_d.png' % (self.kc3id))
        return (ico_n, ico_d)

    def get_local_paths(self):
        path_b = '../cgs/%s.png'
        path_n = os.path.join(DIR_PATH, path_b % (str(self.sid)))
        path_d = os.path.join(DIR_PATH, path_b % (str(self.sid) + "_d"))
        return (path_n, path_d)

    def get_cg(self, ico=False, dmg=False):
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
_IMG_EXCLUSIONS = {147: 'Верный', 361: 'Samuel B. Roberts', 321: 'Kasuga Maru',
                   161: 'Akitsu Maru'}

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
    def __init__(self, discriminator, full_name, resource_mult=1.0):
        self.discriminator = discriminator
        self.full_name = full_name
        self.resource_mult = resource_mult
        ALL_SHIP_TYPES.append(self)

    def __str__(self):
        return self.full_name

TYPE_DESTROYER = ShipType("DD", "Destroyer", resource_mult=0.5)
TYPE_LIGHT_CRUISER = ShipType("CL", "Light Cruiser", resource_mult=0.75)
TYPE_TORPEDO_CRUISER = ShipType("CLT", "Torpedo Cruiser", resource_mult=1.5)
TYPE_HEAVY_CRUISER = ShipType("CA", "Heavy Cruiser", resource_mult=1.5)
TYPE_AVIATION_CRUISER = ShipType("CAV", "Aviation Cruiser", resource_mult=1.5)
TYPE_BATTLESHIP = ShipType("BB", "Battleship", resource_mult=3.0)
TYPE_FAST_BATTLESHIP = ShipType("FBB", "Fast Battleship", resource_mult=3.0)
TYPE_AVIATION_BATTLESHIP = ShipType("BBV", "Aviation Battleship", resource_mult=3.0)
TYPE_LIGHT_CARRIER = ShipType("CVL", "Light Carrier", resource_mult=1.25)
TYPE_CARRIER = ShipType("CV", "Carrier", resource_mult=2)
TYPE_ARMORED_CARRIER = ShipType("CVB", "Armored Carrier", resource_mult=2.25)
TYPE_SEAPLANE_TENDER = ShipType("AV", "Seaplane Tender")
TYPE_SUBMARINE = ShipType("SS", "Submarine", resource_mult=0.4)
TYPE_AIRCRAFT_CARRYING_SUBMARINE = ShipType("SSV", "Aircraft Carrying Submarine", resource_mult=0.5)
TYPE_AMPHIBIOUS_ASSAULT_SHIP = ShipType("LHA", "Amphibious Assault Ship")
TYPE_REPAIR_SHIP = ShipType("AR", "Repair Ship")
TYPE_SUBMARINE_TENDER = ShipType("AS", "Submarine Tender", resource_mult=0.5)
TYPE_TRAINING_CRUISER = ShipType("CT", "Training Cruiser")
TYPE_FLEET_OILER = ShipType("AO", "Fleet Oiler")
TYPE_DESTROYER_ESCORT = ShipType("DE", "Coastal Defense Ship", resource_mult=0.5)

def get_ship_type(discrim):
    r = [x for x in ALL_SHIP_TYPES if x.discriminator == discrim]
    if len(r) > 0:
        return r[0]
    return None

def get_all_ships(allow_remodel=True, only_droppable=False, only_craftable=False, type_discrims=None):
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
            if (type_discrims and not ins.stype in type_discrims):
                continue
            ret.append(ins)

    return ret
