import sys
sys.path.append("../kantaibot/")
import ship_stats
import sqlite3
import os
import htmlparsing
import json
from PIL import Image
import urllib.request
from io import BytesIO
import base64

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
DB_PATH = os.path.join(DIR_PATH, "../kantaidb.db") # hidden to git

HOME_DIR = os.path.expanduser("~")

def get_connection():
    return sqlite3.connect(DB_PATH)

def register_ship_to_database(conn, ship_id, add_images=True):
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

    def get_ship_id(kcid):
        for entry in db_data:
            if entry['id'] == int(kcid):
                return entry['no']

    def get_kc3_data(kcid):
        for entry in db_data:
            if entry['id'] == int(kcid):
                return entry

    def get_ship_info(kcid, entry=None):
        if (not entry):
            entry = get_kc3_data(kcid)
        sname = entry['name']['ja_jp'] if len(entry['name']['ja_romaji']) == 0 else entry['name']['ja_romaji']
        tname = sname
        for o, t in ship_stats.SHIP_TRANSLATIONS.items():
            tname = tname.replace(o, t)
        sname = sname.title()
        tname = tname.title()
        stype = entry['type']
        srarity = entry['rare']
        r_into = None
        r_from = None
        r_level = None
        if ('remodel' in entry):
            rmdl = entry['remodel']
            if ('next' in rmdl):
                r_into = get_ship_id(rmdl['next'])
                r_level = get_ship_id(rmdl['next_lvl'])
            if ('prev' in rmdl):
                r_from = get_ship_id(rmdl['prev'])
        suffix = 0
        if 'suffix' in entry['name'] and entry['name']['suffix']:
            suffix = ship_stats.SHIP_SUFFIXES[entry['name']['suffix']]
            sname += " " + suffix
            tname += " " + suffix
        return sname, tname, stype, srarity, r_into, r_from, r_level


    kc3_id = get_kc3_id(ship_id)
    kc3_entry = get_kc3_data(kc3_id)
    ship_name, translated_name, ship_type, ship_rarity, remodels_into, remodels_from, remodel_level = get_ship_info(kc3_id, kc3_entry)
    if (kc3_id == 0):
        print("ID not found")
        exit()
    type_discrim = ship_stats.get_ship_type(ship_type).discriminator
    print("Found ship '%s' of type %s with KC3 ID %s" % (ship_name, type_discrim, kc3_id))

    # kcwiki data
    def perform_search(tname, stype, kcid):
        print("Fetching images from Kancolle Wiki '%s'..." % tname)
        typeobj = ship_stats.get_ship_type(stype)
        imgs = htmlparsing.get_images_on_wiki_page(tname)
        s_name = tname
        if (get_ship_id(kcid) in [147]): # Bep's images are in Russian
            s_name = ship_name
            print([x for x, y in imgs.items() if '147' in x])
        img_name_reg = "%s %s %03d Full" % (typeobj.discriminator, s_name, int(kcid))
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

    if (add_images):
        img_small_path = "%s/assets/img/ships/%s.png" % (kc3_file_path, kc3_id)
        img_small_damaged_path = "%s/assets/img/ships/%s_d.png" % (kc3_file_path, kc3_id)

        img_reg, img_dmg = perform_search(translated_name, ship_type, kc3_id)
        if (not img_reg or not img_dmg):
            print("One or more images not found")
            if ('prev' in kc3_entry['remodel']):
                prev_id = kc3_entry['remodel']['prev']
                print("Checking previous remodel...")
                pname, ptname, ptype, prarity, pinto, pfrom, prlevel = get_ship_info(prev_id)
                img_reg, img_dmg = perform_search(ptname, ptype, prev_id)
                if (not img_reg or not img_dmg):
                    print("!! Could not find missing images")

        def img_from_url(url):
            req = urllib.request.urlopen(url)
            imgdata = Image.open(BytesIO(req.read())).convert('RGBA')
            return imgdata

        def encode_image(img):
            buf = BytesIO()
            img.save(buf, format="PNG")
            enc = base64.b64encode(buf.getvalue()).decode()
            return enc

        print("Encoding images...")

        if (img_reg and img_dmg):
            # download images and resave as PNG
            enc_reg = encode_image(img_from_url(img_reg))
            enc_dmg = encode_image(img_from_url(img_dmg))

        enc_small_reg = encode_image(Image.open(img_small_path))
        enc_small_dmg = encode_image(Image.open(img_small_damaged_path))


    print("Querying database...")

    if (add_images):
        query = "REPLACE INTO ShipBase (ShipID, Name, Rarity, ShipType, Image_Default, Image_Damaged, Image_Small, Image_Small_Damaged, Remodels_From, Remodels_Into, Remodel_Level)"\
                " VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');"
        query = query % (ship_id, ship_name, ship_rarity, ship_type, enc_reg, enc_dmg, enc_small_reg, enc_small_dmg, remodels_from, remodels_into, remodel_level)
    else:
        query = "UPDATE ShipBase SET Name='%s', Rarity='%s', ShipType='%s', Remodels_From='%s', Remodels_Into='%s', Remodel_Level='%s' WHERE ShipID='%s';"
        query = query % (ship_name, ship_rarity, ship_type, remodels_from, remodels_into, remodel_level, ship_id)
    cur = conn.cursor()
    cur.execute(query)
    cur.close()

    print("Added to database")


id = input("Ship ID: ")
conn = get_connection()
register_ship_to_database(conn, id, add_images=True)
#for id in range(1, 1600):
#    try:
#        register_ship_to_database(conn, id, add_images=False)
#    except:
#        print ("Error handling ID %s: %s" % (id, sys.exc_info()[0]))
conn.commit()
