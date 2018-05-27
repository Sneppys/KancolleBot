"""Handles fleet training."""
import ship_stats
import random

SUCCESS_THRESHOLD = 0.6
ALL_RANKS = []


class TrainingRank():
    """Represents a possible rank from training."""

    def __init__(self, symbol, min_weight, exp_mult):
        """Initialize the rank.

        Parameters
        ----------
        symbol : str
            The letter(s) to use when displaying the rank.
        min_weight : float
            The minimum weight from 0-1 that is required to obtain this rank.
        exp_mult : float
            The multiplier for base EXP to use when obtaining this rank.
        """
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
    """Get the maximum rank possible with the given minimum weight."""
    weight = min(1.0, max(weight, 0.0))
    ranks = [x for x in ALL_RANKS if weight >= x.min_weight]
    ranks.sort(key=lambda x: x.min_weight)
    return ranks.pop()


def inv_lerp(x, low, high):
    """Return a value based on how much x is between low and high.

    0 if x == low, 1 if x == high, linear interpolation between.
    """
    return (x - low) / (high - low)


ALL_DIFFICULTIES = []


class TrainingDifficulty():
    """Represents a difficulty used for training."""

    def __init__(self, name, avg_lvl, min_flag, exp_reward_base,
                 exp_reward_split):
        """Initialize the difficulty.

        Parameters
        ----------
        name : str
            The name of this difficulty.
        avg_lvl : int
            The recommended minimum fleet level to pass this difficulty.
        min_flag : int
            The minimum required fleet level needed to train on this
            difficulty.
        exp_reward_base : int
            The base EXP to award to every ship in the fleet.
        exp_reward_split : int
            The base EXP to split between all members of the fleet.
        """
        self.name = name
        self.avg_lvl = avg_lvl
        self.min_flag = min_flag
        self.exp_reward_base = exp_reward_base
        self.exp_reward_split = exp_reward_split
        ALL_DIFFICULTIES.append(self)

    def rank_training(self, fleet):
        """Return a rank based on the fleet when training on the difficulty."""
        if (len(fleet.ships) == 0):
            return get_rank(0)
        ins = fleet.get_ship_instances()
        sum_lvl = sum(x.level for x in ins)
        avg_lvl = sum_lvl // len(fleet.ships)
        # auto S if fleet > 50% avg lvl of difficulty
        if (avg_lvl >= self.avg_lvl * 1.5):
            return get_rank(1)
        if (avg_lvl >= self.avg_lvl):  # must succeed if fleet > avg lvl
            avg_weight = SUCCESS_THRESHOLD + (1 - SUCCESS_THRESHOLD) / 2
            wgt = random.gauss(avg_weight, (1 - SUCCESS_THRESHOLD) / 2) \
                + inv_lerp(avg_lvl, self.avg_lvl, self.avg_lvl * 1.5) \
                * (1 - SUCCESS_THRESHOLD) / 2
            wgt = max(SUCCESS_THRESHOLD, min(1.0, wgt))
            return get_rank(wgt)
        wgt = inv_lerp(avg_lvl, 0, self.avg_lvl) * (SUCCESS_THRESHOLD * 0.67)
        return get_rank(abs(random.gauss(0, SUCCESS_THRESHOLD * 0.33)) + wgt)

    # returns tuple of (fuel, ammo, steel, bauxite) costs
    def resource_costs(self, fleet):
        """Return the resource cost for training on this difficulty.

        Returns
        tuple
            4-tuple of fuel, ammo, steel, bauxite
        """
        base = (10, 15, 0, 0)
        ins = fleet.get_ship_instances()
        mult = sum([ship_stats.get_ship_type(x.base().stype)
                    .resource_mult for x in ins])
        return tuple(map(lambda x: x * mult, base))


TrainingDifficulty("Simple", 1, 1, 350, 50)
TrainingDifficulty("Easy", 10, 5, 700, 100)
TrainingDifficulty("Medium", 20, 10, 1000, 100)
TrainingDifficulty("Hard", 35, 15, 2500, 500)
TrainingDifficulty("Difficult", 45, 20, 6000, 1000)
TrainingDifficulty("Extreme", 65, 40, 10000, 2000)
