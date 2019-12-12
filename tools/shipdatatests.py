"""Tests that all data in the ships json file is valid"""
import json
import os
import sys

with open(os.path.join(os.path.dirname(__file__), '../ships.json'), 'r', encoding='utf-8') as jsonfile:
    data = json.load(jsonfile)


def warn(sid, text):
    print(f"WARNING[{sid}]: " + text)


def error(sid, text):
    print(f"ERROR[{sid}]: " + text)


def testunique(tset, val):
    if (val not in tset):
        tset.add(val)
        return True
    return False


names = set()
kc3ids = set()
imgsets = [set(), set()]

for sid, ship in data.items():
    try:
        if (ship['images']['full']['file_name'] != f'{sid}.png'):
            warn(sid, "Full image file name not preferred format")
        if (ship['images']['full_damaged']['file_name'] != f'{sid}_d.png'):
            warn(sid, "Damaged full image file name not preferred format")

        kc3id = int(ship['kc3id'])

        if (ship['images']['small']['file_name'] != f'{kc3id}.png'):
            warn(sid, "Small image file name not preferred format")
        if (ship['images']['small_damaged']['file_name'] != f'{kc3id}_d.png'):
            warn(sid, "Small damaged image file name not preferred format")

        if not testunique(names, ship['name']):
            error(sid, "Ship name not unique")

        if not testunique(kc3ids, kc3id):
            error(sid, "KC3ID not unique")

        if not testunique(imgsets[0], ship['images']['full']['url']):
            to_warn = True
            # ignore warning if previous remodel has same image
            if (ship['remodels_from']):
                if (data[str(ship['remodels_from'])]['images']['full']['url'] == ship['images']['full']['url']):
                    to_warn = False
            if to_warn:
                warn(sid, "Full image not unique")
        if not testunique(imgsets[1], ship['images']['full_damaged']['url']):
            to_warn = True
            # ignore warning if previous remodel has same image
            if (ship['remodels_from']):
                if (data[str(ship['remodels_from'])]['images']['full_damaged']['url'] == ship['images']['full_damaged']['url']):
                    to_warn = False
            if to_warn:
                warn(sid, "Full damage image not unique")

        if (ship['remodels_from']):
            rsh = data[str(ship['remodels_from'])]
            if not rsh:
                error(sid, "Remodels-from target does not exist")
            else:
                if (rsh['remodels_into'] == None or rsh['remodel_level'] == None):
                    error(sid, "Previous remodel target does not have sufficient info for remodel")
                if (rsh['remodels_into'] != int(sid)):
                    error(sid, "Previous remodel target does not have ship listed as its target")
        if (ship['remodels_into']):
            rsh = data[str(ship['remodels_into'])]
            if not rsh:
                error(sid, "Remodel target does not exist")
            else:
                if (rsh['remodels_from'] == None or rsh['remodels_from'] != int(sid)):
                    error(sid, "Remodel target does not have ship listed as its previous target")
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error(sid, f"FATAL: Parsing error ({exc_type}); {exc_value}")
