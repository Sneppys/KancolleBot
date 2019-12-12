"""Updates the ship file with any changes needed."""
import json
import os

with open(os.path.join(os.path.dirname(__file__), '../ships.json'), 'r', encoding='utf-8') as jsonfile:
    data = json.load(jsonfile)


def modify(sid, ship_data):
    """Do any changes needed to the ship data."""
    return ship_data


new_data = {}
for sid, ship in data.items():
    mod_data = modify(sid, ship)
    new_data[int(sid)] = mod_data

with open('../ships_mod.json', 'w', encoding='utf-8') as jsonfile:
    jsonfile.write(json.dumps(new_data, sort_keys=True, indent=4))
