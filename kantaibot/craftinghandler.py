import ship_stats

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

RECIPE_BASIC = BaseRecipe(30, 30, 30, 30, 2, [ship_stats.TYPE_DESTROYER,
                                    ship_stats.TYPE_LIGHT_CRUISER])
RECIPE_CVL = BaseRecipe(50, 30, 150, 300, 4, [ship_stats.TYPE_LIGHT_CARRIER])
RECIPE_RARE_DD = BaseRecipe(250, 30, 200, 30, 4, [ship_stats.TYPE_DESTROYER,
                                        ship_stats.TYPE_LIGHT_CRUISER,
                                        ship_stats.TYPE_HEAVY_CRUISER])


# returns list of tuples with (recipe, distSq)
def nearest_n_recipes(f, a, s, b, n=3):
    rlist = RECIPE_LIST
    # maps each recipe to (recipe, distance)
    dist = list(map(lambda x: (x, (f - x.f) ** 2 + (a - x.a) ** 2 + (s - x.s) ** 2 + (b - x.b) ** 2), rlist))
    dist.sort(key=lambda x: x[1])
    n = max(n, len(dist))
    return dist[:n]

# TODO: grab nearest X recipes based on distance, use distance to
# normalize the rarity and class contributions of those recipes
# by boosting the drop chances respectively
# (also reminder not to go overboard with rarity contributions, just small bonus)
def get_craft_from_resources(f, a, s, b):
    nnr = nearest_n_recipes(f, a, s, b)

    weight_bonus_shiptype = []
