import ship_stats
import userinfo
import random

SUCCESS_THRESHOLD = 0.6
ALL_RANKS = []
class TrainingRank():
    def __init__(self, symbol, min_weight, exp_mult):
        self.symbol = symbol
        self.is_success = min_weight >= SUCCESS_THRESHOLD
        self.min_weight = min_weight
        self.exp_mult = exp_mult
        ALL_RANKS.append(self)

TrainingRank('D', 0, 0.1)
TrainingRank('C', 0.4, 0.2)
TrainingRank('B', 0.6, 0.7)
TrainingRank('A', 0.8, 1.0)
TrainingRank('S', 0.9, 1.2)

def get_rank(weight):
    weight = min(1.0, max(weight, 0.0))
    ranks = [x for x in ALL_RANKS if weight >= x.min_weight]
    ranks.sort(key=lambda x: x.min_weight)
    return ranks.pop()

def inv_lerp(x, low, high):
    return (x - low) / (high - low)

ALL_DIFFICULTIES = []
class TrainingDifficulty():
    def __init__(self, name, avg_lvl, min_flag, exp_reward_base, exp_reward_split):
        self.name = name
        self.avg_lvl = avg_lvl
        self.min_flag = min_flag
        self.exp_reward_base = exp_reward_base
        self.exp_reward_split = exp_reward_split
        ALL_DIFFICULTIES.append(self)

    def rank_training(self, fleet):
        if (len(fleet.ships) == 0):
            return get_rank(0)
        ins = fleet.get_ship_instances()
        sum_lvl = sum(x.level for x in ins)
        flag_lvl = ins[0].level
        avg_lvl = sum_lvl // len(fleet.ships)
        if (avg_lvl >= self.avg_lvl * 1.5): # auto S if fleet > 50% avg lvl of difficulty
            return get_rank(1)
        if (avg_lvl >= self.avg_lvl): # must succeed if fleet > avg lvl
            avg_weight = SUCCESS_THRESHOLD + (1 - SUCCESS_THRESHOLD) / 2
            wgt = random.gauss(avg_weight, (1 - SUCCESS_THRESHOLD) / 2) + inv_lerp(avg_lvl, self.avg_lvl, self.avg_lvl * 1.5) * (1 - SUCCESS_THRESHOLD) / 2
            wgt = max(SUCCESS_THRESHOLD, min(1.0, wgt))
            return get_rank(wgt)
        wgt = inv_lerp(avg_lvl, 0, self.avg_lvl) * (SUCCESS_THRESHOLD * 0.67)
        return get_rank(abs(random.gauss(0, SUCCESS_THRESHOLD * 0.33)) + wgt)

    # returns tuple of (fuel, ammo, steel, bauxite) costs
    def resource_costs(self, fleet):
        base = (10, 15, 0, 0)
        ins = fleet.get_ship_instances()
        mult = sum([ship_stats.get_ship_type(x.base().shiptype).resource_mult for x in ins])
        return tuple(map(lambda x: x * mult, base))

TrainingDifficulty("Simple", 1, 1, 350, 50)
TrainingDifficulty("Easy", 10, 5, 700, 100)
TrainingDifficulty("Medium", 20, 10, 1000, 100)
TrainingDifficulty("Hard", 35, 15, 2500, 500)
TrainingDifficulty("Difficult", 45, 20, 6000, 1000)
TrainingDifficulty("Extreme", 65, 40, 10000, 2000)
