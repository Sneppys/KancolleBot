"""Handles crafting logic and recipes."""
import ship_stats
import math
import drophandler
import os
import json


DIR_PATH = os.path.dirname(os.path.realpath(__file__))
RECIPE_LIST = []

_json_cache = {}


def read_json(filepath):
    """Return the JSON inside of the given JSON file."""
    if (filepath in _json_cache):
        return _json_cache[filepath]
    with open(filepath, 'r', encoding='utf-8') as fileinfo:
        data = json.load(fileinfo)
        _json_cache[filepath] = data
        return data


RECIPE_DATA_FILE = os.path.join(DIR_PATH, "../recipes.json")
RECIPE_DATA = read_json(RECIPE_DATA_FILE)

WEIGHT_BONUS_TYPE = RECIPE_DATA['weight_bonus_type']
WEIGHT_BONUS_RARITY = RECIPE_DATA['weight_bonus_rarity']


class BaseRecipe():
    """Recipe for crafting."""

    def __init__(self, f, a, s, b, rarityfocus, types):
        """Initialize the recipe.

        Parameters
        ----------
        f : int
            Fuel amount for the recipe.
        a : int
            Ammo amount for the recipe.
        s : int
            Steel amount for the recipe.
        b : int
            Bauxite amount for the recipe.
        rarityfocus : int
            The rarity to add weight to when crafting with this recipe.
        types : list
            List of ship types to add weight to when craftinh with this recipe.
        """
        self.f = f
        self.a = a
        self.s = s
        self.b = b
        self.types = types
        self.rarityfocus = rarityfocus
        RECIPE_LIST.append(self)


for recipe in RECIPE_DATA['recipes']:
    rs = recipe['resources']
    ra = recipe['rarity']
    ty = recipe['types']
    types = [ship_stats.get_ship_type(t) for t in ty]
    BaseRecipe(rs[0], rs[1], rs[2], rs[3], ra, types)


# returns list of tuples with (recipe, distSq)
def nearest_n_recipes(f, a, s, b, n=3):
    """Return the closest n recipes by distance to the given resources."""
    rlist = RECIPE_LIST
    # maps each recipe to (recipe, distance)
    dist = list(map(lambda x: (x,
                               (f - x.f) ** 2 + (a - x.a) ** 2
                               + (s - x.s) ** 2 + (b - x.b) ** 2), rlist))
    dist.sort(key=lambda x: x[1])
    n = min(n, len(dist))
    return dist[:n]


def get_craft_from_resources(owner, f, a, s, b):
    """Get a random ship craft given the resource amounts to use."""
    nnr = nearest_n_recipes(f, a, s, b)

    # this is complicated so here's a simple explanation:
    # in (n - 1) steps where n is # of recipes taken from above:
    #   - take closest remaining recipe based on distance
    #   - get % of total distance of remaining recipes closest takes up
    #   - remove closest from list, add it with its % to the final list
    #   - scale next steps' % based on how much % the previous steps' closest
    #        were
    # after, take the last remaining value and set its # so everything equals 1
    dist_map = list(map(lambda x: (x[0], math.sqrt(x[1])), nnr))
    final_map = []
    pcnt_left = 1.0
    for i in range(len(nnr) - 1):
        total_dist = sum(map(lambda x: x[1], dist_map))
        if (total_dist == 0):
            break
        dist_map_inv = list(map(lambda x: (x[0], pcnt_left
                                           * (total_dist - x[1]) / total_dist),
                                dist_map))
        dist_map.sort(key=lambda x: -x[1])
        dist_map_inv.sort(key=lambda x: x[1])
        app = dist_map_inv.pop()
        pcnt_left -= app[1]
        final_map.append(app)
        dist_map.pop()
    total_pcnt = sum(map(lambda x: x[1], final_map))
    last = dist_map.pop()
    final_map.append((last[0], 1 - total_pcnt))

    weight_bonus_shiptype = list(map(
        lambda x: (x[0], int(x[1] * WEIGHT_BONUS_TYPE)), final_map))
    weight_bonus_rarity = list(map(
        lambda x: (x[0], int(x[1] * WEIGHT_BONUS_RARITY)), final_map))

    weight_boost = {}

    all_types = []
    for recipe, _m in final_map:
        all_types.extend(map(lambda x: x.discriminator, recipe.types))
    applicable_ships = set(ship_stats.get_all_ships(allow_remodel=False,
                                                    only_craftable=True,
                                                    type_discrims=all_types))

    # shiptype boost
    for recipe, weight_bonus in weight_bonus_shiptype:
        award_base = weight_bonus // len(applicable_ships)
        for s in applicable_ships:
            if (s.sid not in weight_boost):
                weight_boost[s.sid] = 0
            weight_boost[s.sid] += award_base

    # rarity boost (only for shiptypes above)
    # boost based on dist to rarity focus (max 2)
    for recipe, weight_bonus in weight_bonus_rarity:
        inv_dist = list(map(
            lambda x: (x, 2 - abs(recipe.rarityfocus - x.rarity)),
            applicable_ships))
        rarity_total = sum([x[1] for x in inv_dist if x[1] > 0])
        rarity_award = weight_bonus // rarity_total
        for s, rd in inv_dist:
            if (rd <= 0):
                continue
            weight_boost[s.sid] += rarity_award * rd

    def weight_function(ship):
        wb = ship.sid in weight_boost and weight_boost[ship.sid] > 0
        return (drophandler.get_basic_weight(ship) // (.5 if wb else 3)) \
            + (weight_boost[ship.sid] if wb else 0)
    drop = drophandler.get_random_drop(owner, weight_function=weight_function,
                                       only_craftable=True)
    return drop
