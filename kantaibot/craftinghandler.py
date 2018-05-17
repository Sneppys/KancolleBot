import ship_stats
import math
import drophandler
import os
import sqlite3

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
DB_PATH = os.path.join(DIR_PATH, "../kantaidb.db") # hidden to git

def get_connection():
    return sqlite3.connect(DB_PATH)

# basic recipe for crafting
RECIPE_LIST = []
class BaseRecipe():
    def __init__(self, f, a, s, b, rarityfocus, types):
        self.f = f
        self.a = a
        self.s = s
        self.b = b
        self.types = types
        self.rarityfocus = rarityfocus
        RECIPE_LIST.append(self)

BaseRecipe(30, 30, 30, 30, 2, [ship_stats.TYPE_DESTROYER,
                               ship_stats.TYPE_LIGHT_CRUISER])
BaseRecipe(250, 130, 200, 30, 2, [ship_stats.TYPE_DESTROYER,
                                  ship_stats.TYPE_LIGHT_CRUISER,
                                  ship_stats.TYPE_SUBMARINE,
                                  ship_stats.TYPE_HEAVY_CRUISER])
BaseRecipe(300, 30, 150, 400, 2, [ship_stats.TYPE_LIGHT_CARRIER,
                                  ship_stats.TYPE_SEAPLANE_TENDER])
BaseRecipe(250, 30, 200, 30, 3, [ship_stats.TYPE_DESTROYER,
                                 ship_stats.TYPE_LIGHT_CRUISER,
                                 ship_stats.TYPE_HEAVY_CRUISER,
                                 ship_stats.TYPE_SUBMARINE,
                                 ship_stats.TYPE_TRAINING_CRUISER])
BaseRecipe(270, 30, 330, 130, 2, [ship_stats.TYPE_HEAVY_CRUISER,
                                  ship_stats.TYPE_SUBMARINE,
                                  ship_stats.TYPE_DESTROYER])
BaseRecipe(400, 100, 600, 30, 2, [ship_stats.TYPE_HEAVY_CRUISER,
                                 ship_stats.TYPE_BATTLESHIP,
                                 ship_stats.TYPE_FAST_BATTLESHIP,
                                 ship_stats.TYPE_LIGHT_CRUISER])
BaseRecipe(500, 30, 600, 30, 4, [ship_stats.TYPE_HEAVY_CRUISER,
                                 ship_stats.TYPE_BATTLESHIP,
                                 ship_stats.TYPE_LIGHT_CRUISER])
BaseRecipe(300, 30, 400, 300, 3, [ship_stats.TYPE_LIGHT_CARRIER,
                                  ship_stats.TYPE_CARRIER,
                                  ship_stats.TYPE_SEAPLANE_TENDER])
BaseRecipe(350, 30, 400, 400, 3, [ship_stats.TYPE_LIGHT_CARRIER,
                                  ship_stats.TYPE_CARRIER,
                                  ship_stats.TYPE_SEAPLANE_TENDER])
BaseRecipe(300, 300, 600, 600, 4, [ship_stats.TYPE_CARRIER,
                                   ship_stats.TYPE_LIGHT_CARRIER])
BaseRecipe(400, 200, 500, 700, 4, [ship_stats.TYPE_CARRIER,
                                   ship_stats.TYPE_LIGHT_CARRIER])
BaseRecipe(1000, 1000, 1000, 200, 5, [ship_stats.TYPE_BATTLESHIP,
                                      ship_stats.TYPE_FAST_BATTLESHIP,
                                      ship_stats.TYPE_HEAVY_CRUISER])
BaseRecipe(2000, 2000, 2000, 2000, 5, [ship_stats.TYPE_HEAVY_CRUISER,
                                       ship_stats.TYPE_BATTLESHIP,
                                       ship_stats.TYPE_FAST_BATTLESHIP,
                                       ship_stats.TYPE_FLEET_OILER,
                                       ship_stats.TYPE_SUBMARINE_TENDER])
BaseRecipe(1500, 1500, 2000, 1000, 5, [ship_stats.TYPE_BATTLESHIP,
                                       ship_stats.TYPE_FAST_BATTLESHIP,
                                       ship_stats.TYPE_HEAVY_CRUISER,
                                       ship_stats.TYPE_LIGHT_CRUISER])
BaseRecipe(3000, 1500, 4000, 3000, 6, [ship_stats.TYPE_LIGHT_CARRIER,
                                       ship_stats.TYPE_CARRIER,
                                       ship_stats.TYPE_ARMORED_CARRIER])
BaseRecipe(4000, 2000, 5500, 7000, 6, [ship_stats.TYPE_ARMORED_CARRIER,
                                       ship_stats.TYPE_CARRIER,
                                       ship_stats.TYPE_AMPHIBIOUS_ASSAULT_SHIP])
BaseRecipe(5000, 6000, 6000, 3000, 6, [ship_stats.TYPE_BATTLESHIP,
                                       ship_stats.TYPE_AMPHIBIOUS_ASSAULT_SHIP])


# returns list of tuples with (recipe, distSq)
def nearest_n_recipes(f, a, s, b, n=3):
    rlist = RECIPE_LIST
    # maps each recipe to (recipe, distance)
    dist = list(map(lambda x: (x, (f - x.f) ** 2 + (a - x.a) ** 2 + (s - x.s) ** 2 + (b - x.b) ** 2), rlist))
    dist.sort(key=lambda x: x[1])
    n = min(n, len(dist))
    return dist[:n]

def get_craft_from_resources(owner, f, a, s, b):
    nnr = nearest_n_recipes(f, a, s, b)

    total_weight_bonus_shiptype = 50000
    total_weight_bonus_rarity = 50000

    # this is complicated so here's a simple explanation:
    # in (n - 1) steps where n is # of recipes taken from above:
    #   - take closest remaining recipe based on distance
    #   - get % of total distance of remaining recipes closest takes up
    #   - remove closest from list, add it with its % to the final list
    #   - scale next steps' % based on how much % the previous steps' closest were
    # after, take the last remaining value and set its # so everything equals 1
    dist_map = list(map(lambda x: (x[0], math.sqrt(x[1])), nnr))
    final_map = []
    pcnt_left = 1.0
    for i in range(len(nnr) - 1):
        total_dist = sum(map(lambda x: x[1], dist_map))
        if (total_dist == 0):
            break
        dist_map_inv = list(map(lambda x: (x[0], pcnt_left * (total_dist - x[1]) / total_dist), dist_map))
        dist_map.sort(key=lambda x: -x[1])
        dist_map_inv.sort(key=lambda x: x[1])
        app = dist_map_inv.pop()
        pcnt_left -= app[1]
        final_map.append(app)
        dist_map.pop()
    total_pcnt = sum(map(lambda x: x[1], final_map))
    last = dist_map.pop()
    final_map.append((last[0], 1 - total_pcnt))

    weight_bonus_shiptype = list(map(lambda x: (x[0], int(x[1] * total_weight_bonus_shiptype)), final_map))
    weight_bonus_rarity = list(map(lambda x: (x[0], int(x[1] * total_weight_bonus_rarity)), final_map))

    weight_boost = {}

    all_types = []
    for recipe, _m in final_map:
        all_types.extend(map(lambda x: x.discriminator, recipe.types))
    conn = get_connection()
    cur = conn.cursor()
    applicable_ships = set(ship_stats.get_all_ships(allow_remodel=False, only_craftable=True, type_discrims=all_types))

    # shiptype boost
    for recipe, weight_bonus in weight_bonus_shiptype:
        award_base = weight_bonus // len(applicable_ships)
        for s in applicable_ships:
            if (not s.sid in weight_boost):
                weight_boost[s.sid] = 0
            weight_boost[s.sid] += award_base

    # rarity boost (only for shiptypes above)
    # boost based on dist to rarity focus (max 2)
    for recipe, weight_bonus in weight_bonus_rarity:
        inv_dist = list(map(lambda x: (x, 2 - abs(recipe.rarityfocus - x.rarity)), applicable_ships))
        rarity_total = sum([x[1] for x in inv_dist if x[1] > 0])
        rarity_award = weight_bonus // rarity_total
        for s, rd in inv_dist:
            if (rd <= 0):
                continue
            weight_boost[s.sid] += rarity_award * rd

    def weight_function(ship):
        wb = ship.sid in weight_boost and weight_boost[ship.sid] > 0
        return (drophandler.get_basic_weight(ship) // (.5 if wb else 3)) + (weight_boost[ship.sid] if wb else 0)
    drop = drophandler.get_random_drop(owner, weight_function=weight_function, only_craftable=True, cur=cur)
    cur.close()
    conn.commit()
    return drop
