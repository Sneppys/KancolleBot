"""Utility for adding ship CGs to the seasonal file."""
import json
import os

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
SHIP_DATA_FILE = os.path.join(DIR_PATH, "../ships.json")
SEASONAL_DATA_FILE = os.path.join(DIR_PATH, "../seasonal.json")

with open(SHIP_DATA_FILE, 'r') as shipdata:
    SHIP_DATA = json.load(shipdata)

while True:
    name = input("Name: ")
    sid, entry = next((k, x) for k, x in SHIP_DATA.items() if x['name'] == name)
    with open(SEASONAL_DATA_FILE, 'r') as seasonaldata:
        data = json.load(seasonaldata)

    url_b = input("Base CG URL: ")
    url_d = input("Damaged CG URL: ")

    set = {'images': entry['images']}
    set['images']['full']['file_name'] = "%sf.png" % str(sid)
    set['images']['full']['url'] = url_b
    set['images']['full_damaged']['file_name'] = "%sf_d.png" % str(sid)
    set['images']['full_damaged']['url'] = url_d
    data[sid] = set

    with open(SEASONAL_DATA_FILE, 'w') as seasonaldata:
        json.dump(data, seasonaldata, indent=4, sort_keys=True)

    print("Dumped %s, need icos for %s" % (sid, entry['kc3id']))
