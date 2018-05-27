"""Handles random ship drops."""
import ship_stats
import random
import os

DIR_PATH = os.path.dirname(os.path.realpath(__file__))


def get_basic_weight(ship):
    """Get the base weight for a ShipBase."""
    return (9 - ship.rarity) * (10 - ship.rarity) ** 2


def get_random_drop(owner, weight_function=get_basic_weight,
                    only_droppable=False, only_craftable=False):
    """Get a random ship drop, as a ShipInstance.

    Parameters
    ----------
    owner : int
        Discord ID of the owner of the drop.
    weight_function : function
        Function used to determine weight based on passed ShipBase.
    only_droppable : bool
        If True, only select from the ships which can be dropped.
    only_craftable : bool
        If True, only select from the ships which can be crafted.
    """
    ships = ship_stats.get_all_ships(allow_remodel=False,
                                     only_droppable=only_droppable,
                                     only_craftable=only_craftable)

    total_pool = sum(weight_function(s) for s in ships)
    val = random.randrange(total_pool)
    for ship in ships:
        val -= weight_function(ship)
        if (val <= 0):
            return ship_stats.ShipInstance.new(ship.sid, owner)
            break
    return ship_stats.ShipInstance.new(11, owner)


def get_drop_chances(weight_function=get_basic_weight, only_droppable=False,
                     only_craftable=False):
    """Get the chances that each rarity can drop.

    Parameters
    ----------
    weight_function : function
        Function used to determine weight based on passed ShipBase.
    only_droppable : bool
        If True, only select from the ships which can be dropped.
    only_craftable : bool
        If True, only select from the ships which can be crafted.

    Returns
    -------
    list
        List of size 8, floats equalling percent the respective rarity can
        drop.
    """
    ships = ship_stats.get_all_ships(allow_remodel=False,
                                     only_droppable=only_droppable,
                                     only_craftable=only_craftable)

    total_pool = sum(weight_function(s) for s in ships)
    totals = [0] * 8
    for rarity in range(8):
        rtotal = sum(weight_function(s) for s in ships
                     if s.rarity == rarity + 1)
        totals[rarity] = rtotal
    return list(map(lambda x: x / total_pool, totals))
