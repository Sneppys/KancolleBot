"""The main file for the bot."""
import discord
from discord.ext import commands
import asyncio
import imggen
import io
import drophandler
import craftinghandler
import userinfo
import os
import traceback
import sys
import fleet_training
import sorties
import ship_stats
import json
import datetime
import subprocess
import logging
from settings import setting, namesub, setting_random

COMMAND_PREFIX = setting('command_prefix')

bot = commands.Bot(command_prefix=COMMAND_PREFIX, case_insensitive=True,
                   activity=discord.Game(type=0, name=setting('bot_playing')))

DROP_COOLDOWN = setting('cooldowns.drop')
CRAFTING_COOLDOWN = setting('cooldowns.craft')
TRAINING_COOLDOWN = setting('cooldowns.train')


@bot.command(help=namesub("Show a <ship.title> from your inventory"), usage="[Ship ID]")
async def show(ctx, shipid: int):
    """Show the specified ship from the user's inventory."""
    did = ctx.author.id
    inv = userinfo.get_user_inventory(did)
    ins = [x for x in inv.inventory if x.invid == shipid]
    if (len(ins) > 0):
        ship_instance = ins.pop()
        base = ship_instance.base()
        image_file = imggen.generate_ship_card(ctx.bot, ship_instance)
        if (ship_instance.level > setting('levels.level_cap')):
            quote = base.get_quote('married')
        else:
            quote = base.get_quote('idle')
        await ctx.send(file=discord.File(io.BytesIO(image_file.getvalue()),
                                         filename="image.png"),
                       content="%s: *%s*" % (base.name, quote))
    else:
        await ctx.send(namesub("<ship.title> with ID %s not found in your inventory") % (
            shipid))


@bot.command(help="Get a random ship drop, cooldown of 4h",
             hidden=not setting('features.drop_enabled'))
async def drop(ctx):
    """Drop a random ship for the user."""
    did = ctx.author.id
    if (not setting('features.drop_enabled')):
        await ctx.send("That feature is not enabled.")
        return
    if (userinfo.has_space_in_inventory(did)):
        cd = userinfo.check_cooldown(did, 'Last_Drop', DROP_COOLDOWN)
        if (cd == 0):
            drop = drophandler.get_random_drop(did, only_droppable=True)
            ship_base = drop.base()
            ship_name = ship_base.name
            ship_rarity = ship_base.rarity
            rarity = setting('rarities')
            inv = userinfo.get_user_inventory(did)
            inv.add_to_inventory(drop)
            image_file = imggen.generate_ship_card(ctx.bot, drop)

            await ctx.send(
                file=discord.File(
                    io.BytesIO(image_file.getvalue()),
                    filename="image.png"),
                content="%s got %s! (%s)\n\n%s: *%s*" % (
                        ctx.author.display_name, ship_name,
                        rarity[ship_rarity - 1], ship_name,
                        ship_base.get_quote('intro')))
            logging.info("[Drop] %s (%s) received %s from a drop" %
                         (str(ctx.author), did, ship_name))
        else:
            hrs = cd // 3600
            min = cd // 60 % 60
            sec = cd % 60
            await ctx.send("You have %dh%02dm%02ds remaining until you can"
                           " get your next drop" % (hrs, min, sec))
    else:
        await ctx.send(namesub("Your inventory is full! You can scrap a <ship.title> with"
                       " `%sscrap [<ship.title> ID]`") % COMMAND_PREFIX)


@bot.command(help="Show your inventory", usage="(Page #)")
async def inv(ctx, page: int=1):
    """Show the user's inventory."""
    image_file = imggen.generate_inventory_screen(ctx.author, page)
    await ctx.send(file=discord.File(io.BytesIO(image_file.getvalue()),
                                     filename="image.png"))


@bot.command(help=namesub("Craft a <ship.title> with the given resources"),
             usage=namesub("[<fuel.title>] [<ammo.title>] [<steel.title>] [<bauxite.title>]"),
             hidden=not setting('features.crafting_enabled') or not setting('features.resources_enabled'))
async def craft(ctx, fuel: int, ammo: int, steel: int, bauxite: int):
    """Craft a random ship based on the user's inputted resources."""
    did = ctx.author.id
    user = userinfo.get_user(did)
    if (not setting('features.crafting_enabled') or not setting('features.resources_enabled')):
        await ctx.send("That feature is not enabled.")
        return
    if (userinfo.has_space_in_inventory(did)):
        cd = userinfo.check_cooldown(
            did, 'Last_Craft', CRAFTING_COOLDOWN, set_if_off=False)
        if (cd == 0):
            min_craft = setting('resources.min_crafting')
            if (fuel >= min_craft[0] and ammo >= min_craft[1] and
                    steel >= min_craft[2] and bauxite >= min_craft[3]):
                if (user.has_enough(fuel, ammo, steel, bauxite)):
                    craft = craftinghandler.get_craft_from_resources(
                        did, fuel, ammo, steel, bauxite)
                    user.mod_fuel(-fuel)
                    user.mod_ammo(-ammo)
                    user.mod_steel(-steel)
                    user.mod_bauxite(-bauxite)
                    inv = userinfo.get_user_inventory(did)
                    inv.add_to_inventory(craft)
                    # set cooldown
                    userinfo.check_cooldown(
                        did, 'Last_Craft', CRAFTING_COOLDOWN, set_if_off=True)
                    image_file = imggen.generate_ship_card(ctx.bot, craft)
                    ship_base = craft.base()
                    await ctx.send(
                        file=discord.File(io.BytesIO(image_file.getvalue()),
                                          filename="image.png"),
                        content="%s just crafted %s!\n\n%s: *%s*" % (
                            ctx.author.display_name, ship_base.name,
                            ship_base.name, ship_base.get_quote('intro')))
                    logging.info("[Craft] %s (%s) crafted %s using recipe "
                                 "%s/%s/%s/%s" %
                                 (str(ctx.author), did, ship_base.name,
                                  fuel, ammo, steel, bauxite))
                else:
                    await ctx.send("Not enough resources!")
            else:
                await ctx.send("Use at least 30 of each resource")
        else:
            min = cd // 60
            sec = cd % 60
            await ctx.send("You have %dm%02ds remaining until you can craft "
                           "another ship" % (min, sec))
    else:
        await ctx.send(namesub("Your inventory is full! You can scrap a <ship.title> with "
                       "`%sscrap [<ship.title> ID]`") % COMMAND_PREFIX)


@bot.command(help=namesub("Scraps a <ship.title>, removing it for a tiny amount of resources"),
             usage=namesub("[<ship.title> ID]"))
async def scrap(ctx, shipid: int):
    """Scrap the given ship from the user's inventory."""
    did = ctx.author.id
    user = userinfo.get_user(did)
    inv = userinfo.get_user_inventory(did)
    ins = [x for x in inv.inventory if x.invid == shipid]
    if (len(ins) > 0):
        ship_instance = ins.pop()
        base = ship_instance.base()
        user.mod_fuel(setting_random('resources.scrap_gain.fuel'))
        user.mod_ammo(setting_random('resources.scrap_gain.ammo'))
        user.mod_steel(setting_random('resources.scrap_gain.steel'))
        user.mod_bauxite(setting_random('resources.scrap_gain.bauxite'))
        inv.remove_from_inventory(shipid)
        await ctx.send("Scrapped %s... <:roosad:434916104268152853>" % (
            base.name))
        logging.info("[Scrap] %s (%s) scrapped ship %s with inv id %s" %
                     (str(ctx.author), did, base.name, shipid))
    else:
        await ctx.send(namesub("<ship.title> with ID %s not found in your inventory") % (
            shipid))


@bot.command(help=namesub("Shows your inventory, hiding all <ship_plural> except duplicates"),
             usage="(Page #)")
async def dupes(ctx, page: int=1):
    """Show all the ships the user has two or more of."""
    image_file = imggen.generate_inventory_screen(
        ctx.author, page, only_dupes=True)
    await ctx.send(file=discord.File(io.BytesIO(image_file.getvalue()),
                                     filename="image.png"))


@bot.command(help=namesub("Remodel a <ship.title> if it is a high enough level"),
             usage=namesub("[<ship.title> ID]"), hidden=not setting('features.levels_enabled'))
async def remodel(ctx, shipid: int):
    """Remodel the given ship."""
    if (not setting('features.levels_enabled')):
        await ctx.send("That feature is not enabled.")
        return
    did = ctx.author.id
    inv = userinfo.get_user_inventory(did)
    ins = [x for x in inv.inventory if x.invid == shipid]
    if (len(ins) > 0):
        ship_instance = ins.pop()
        base = ship_instance.base()
        if (base.remodels_into):
            if (ship_instance.is_remodel_ready()):
                old_name = base.name
                ship_instance.sid = base.remodels_into
                base = ship_instance.base()
                new_name = base.name
                userinfo.update_ship_sid(ship_instance)
                image_file = imggen.generate_ship_card(ctx.bot, ship_instance)
                await ctx.send(file=discord.File(
                    io.BytesIO(image_file.getvalue()),
                    filename="image.png"),
                               content="%s: *%s*" % (new_name,
                                                     base.get_quote('remodel')
                                                     ))
                logging.info("[Remodel] %s (%s) remodelled %s into %s" %
                             (str(ctx.author), did, old_name, new_name))
            else:
                await ctx.send("%s isn't ready for a remodel just yet." % (
                    base.name))
        else:
            await ctx.send("%s doesn't have another remodel." % (base.name))
    else:
        await ctx.send(namesub("<ship.title> with ID %s not found in your inventory") % (
            shipid))


@bot.command(help=namesub("Show all training difficulties or train your <fleet> on one"),
             usage="(Difficulty #)",
             hidden=(not setting('features.training_enabled') or not setting('features.levels_enabled')
                     or not setting('features.fleets_enabled')))
async def train(ctx, dif: int=-1):
    """Train a user's fleet given the difficulty, or show training options."""
    did = ctx.author.id
    difs = fleet_training.ALL_DIFFICULTIES
    if (not setting('features.training_enabled') or not setting('features.levels_enabled')
            or not setting('features.fleets_enabled')):
        await ctx.send("That feature is not enabled.")
        return
    if (dif == -1):
        description = "Difficulties:\n"
        description += "\n".join([namesub("#%s. %s: Min <flagship> level %s, Recommended"
                                  " <fleet> level %s.") % (x + 1,
                                                           difs[x].name,
                                                           difs[x].min_flag,
                                                           difs[x].avg_lvl)
                                  for x in range(len(difs))])
        footer = "Type %strain (#) to train a fleet with a difficulty" % (
            COMMAND_PREFIX)
        embed = discord.Embed(title=namesub("<fleet.title> Training"), description=description)
        embed.set_footer(text=footer)

        await ctx.send(embed=embed)
    else:
        if (dif > 0 and dif <= len(difs)):
            dif_targ = difs[dif - 1]
            fleet = userinfo.UserFleet.instance(1, did)
            if (len(fleet.ships) > 0):
                ins = fleet.get_ship_instances()
                flag = ins[0]
                if (flag.level >= dif_targ.min_flag):
                    rsc = dif_targ.resource_costs(fleet)
                    rsc = tuple(map(int, rsc))
                    user = userinfo.get_user(did)
                    if (user.has_enough(*rsc)):
                        cd = userinfo.check_cooldown(
                            did, "Last_Training", TRAINING_COOLDOWN)
                        if (cd == 0):
                            # conditions passed
                            rank = dif_targ.rank_training(fleet)

                            exp_rew_base = rank.exp_mult \
                                * dif_targ.exp_reward_base
                            exp_rew_split = rank.exp_mult \
                                * dif_targ.exp_reward_split

                            exp = [exp_rew_base] * len(ins)
                            exp_per = exp_rew_split // len(ins) + 1
                            exp[0] += exp_per
                            exp = list(map(lambda x: x + exp_per, exp))

                            lvl_dif = [x.level for x in ins]
                            for i in range(len(ins)):
                                ins[i].add_exp(exp[i])
                                lvl_dif[i] = ins[i].level - lvl_dif[i]

                            user.mod_fuel(-rsc[0])
                            user.mod_ammo(-rsc[1])
                            user.mod_steel(-rsc[2])
                            user.mod_bauxite(-rsc[3])

                            embed = discord.Embed(title="Training %s" % (
                                "Success" if rank.is_success else "Failed"))
                            embed.color = 65280 if rank.is_success \
                                else 16711680
                            embed.description = "Rank %s | %s Difficulty" % (
                                rank.symbol, dif_targ.name)
                            flag = ins.pop(0)
                            embed.add_field(name="EXP Gain", value=flag.base(
                            ).name + " (*)\n" + "\n".join([x.base().name
                                                           for x in ins]),
                                                           inline=True)
                            embed.add_field(
                                name="--------", value="\n".join(["+%g EXP" % x
                                                                  for x in exp]
                                                                 ))
                            ins.insert(0, flag)
                            embed.add_field(name="--------", value="\n".join(
                                ["Level %s (+%s)" % (ins[i].level, lvl_dif[i])
                                 for i in range(len(ins))]))
                            if (setting('features.resources_enabled')):
                                embed.set_footer(
                                    text=namesub("Used %g <fuel>, %g <ammo>, %g <steel>, %g "
                                                 "<bauxite>") % rsc)

                            await ctx.send(embed=embed)
                            logging.info("[Training] %s (%s) completed "
                                         "training level %s with rank %s" % (
                                            str(ctx.author), did,
                                            dif_targ.name,
                                            rank.symbol))
                        else:
                            hrs = cd // 3600
                            min = cd // 60 % 60
                            sec = cd % 60
                            await ctx.send(namesub("You have %dh%02dm%02ds remaining "
                                                   "until you can train your <fleet> "
                                                   "again") % (hrs, min, sec))
                    else:
                        await ctx.send(namesub("Not enough resources! (Required: %g "
                                       "<fuel>, %g <ammo>, %g <steel>, %g <bauxite>)")
                                       % rsc)
                else:
                    await ctx.send(namesub("<flagship.title> isn't a high enough level! "
                                   "(Needs to be at least %s)") % (
                                       dif_targ.min_flag))
            else:
                await ctx.send(namesub("<fleet.title> %s is empty!") % (1))
        else:
            await ctx.send("No such difficulty #%s" % dif)


@bot.command(help="Show your active cooldowns", aliases=["cd"])
async def cooldowns(ctx):
    """Show how much time left the user has before performing actions."""
    did = ctx.author.id
    cd_check = []
    if (setting('features.drop_enabled')):
        cd_check.append(("Last_Drop", "Drop", DROP_COOLDOWN))
    if (setting('features.training_enabled')):
        cd_check.append(("Last_Training", namesub("<fleet.title> Training"), TRAINING_COOLDOWN))
    if (setting('features.crafting_enabled')):
        cd_check.append(("Last_Craft", "Crafting", CRAFTING_COOLDOWN))
    if (len(cd_check) == 0):
        await ctx.send("That feature is not enabled.")
        return
    msg = "Current cooldowns for %s:\n" % ctx.author.display_name
    msg += "```\n"
    for cd, name, cd_s in cd_check:
        t = userinfo.check_cooldown(did, cd, cd_s, set_if_off=False)
        if (t > 0):
            hrs = t // 3600
            min = t // 60 % 60
            sec = t % 60
            msg += "%s: %dh%02dm%02ds remaining\n" % (name, hrs, min, sec)
        else:
            msg += "%s: Available!\n" % (name)
    msg += "```"
    await ctx.send(msg)


@bot.command(help=namesub("Using a Ring, marry a max level <ship.title> to increase their "
             "level cap"), aliases=["ring"],
             hidden=not setting('features.marriage_enabled') or not setting('features.levels_enabled'))
async def marry(ctx, shipid: int):
    """Allow the user to marry a level 99 ship, increasing its level cap."""
    if (not setting('features.marriage_enabled') or not setting('features.levels_enabled')):
        await ctx.send("This feature is not enabled.")
    did = ctx.author.id
    user = userinfo.get_user(did)
    inv = userinfo.get_user_inventory(did)
    ins = [x for x in inv.inventory if x.invid == shipid]
    if (len(ins) > 0):
        ship_instance = ins.pop()
        base = ship_instance.base()
        if (ship_instance.level == setting('levels.level_cap')):
            ring_req = setting('levels.marriage_ring_required')
            rings = user.rings
            if (rings > 0 or not ring_req):
                ship_instance.level = setting('levels.level_cap') + 1
                ship_instance.exp = 0
                ship_instance.add_exp(0)
                if (ring_req):
                    user.use_ring()
                ship_name = base.name
                image_file = imggen.generate_ship_card(ctx.bot, ship_instance)
                await ctx.send(file=discord.File(
                    io.BytesIO(image_file.getvalue()), filename="image.png"),
                               content="%s: *%s*" % (ship_name,
                                                     base.get_quote('married')
                                                     ))
                logging.info("[Marriage] %s (%s) married their %s" %
                             (str(ctx.author), did, ship_name))
            else:
                await ctx.send("You don't have any more rings.")
        else:
            await ctx.send("%s isn't ready for marriage yet." % (base.name))
    else:
        await ctx.send(namesub("<ship.title> with ID %s not found in your inventory") % (
            shipid))


@bot.command(help=namesub("Show the <sortie> map"), hidden=True)
@commands.is_owner()
async def newmap(ctx):
    """Debug function to show a generated map."""
    sortie = sorties.random_sortie()
    image_file = imggen.generate_sortie_card(sortie)
    await ctx.send(file=discord.File(io.BytesIO(image_file.getvalue()),
                                     filename="image.png"))


@bot.command(help=namesub("Admin command to add a <ship.title> to someone's inventory"),
             hidden=True)
@commands.is_owner()
async def add_ship(ctx, user: discord.Member, ship_name):
    """Admin command to add a ship to a user's inventory."""
    inv = userinfo.get_user_inventory(user.id)
    targ = None
    for ship in ship_stats.get_all_ships():
        if (ship.name.lower() == ship_name.lower() or ship.name.lower()
                .replace(' ', '_') == ship_name.lower()):
            targ = ship
            break
    if (targ):
        ins = ship_stats.ShipInstance.new(targ.sid, user.id)
        inv.add_to_inventory(ins)
        await ctx.send("Added %s to %s's inventory" % (targ.name, str(user)))
        logging.info("[ADMIN_ADD] Added %s to %s's (%s) inventory" %
                     (targ.name, str(user), user.id))
    else:
        await ctx.send(namesub("Cannot find <ship.title> '%s'") % ship_name)


def fleet_strings(inv, fleet_s):
    """Return a list of strings detailing the given fleet's information."""
    ship_ins = list(
        map(lambda x: [y for y in inv.inventory if y.invid == x].pop(),
            fleet_s.ships))
    ship_data = list(map(lambda x: "*%s* (L%02d, %s)" %
                         (x.base().name, x.level, x.base().stype), ship_ins))
    return ship_data


@bot.group(help=namesub("View your <fleet> (Subcommands for <fleet> management)"),
           case_insensitive=True, hidden=not setting('features.fleets_enabled'),
           name=setting('commands.fleet'))
async def fleet(ctx):
    """Base command for fleet management, shows the current fleet."""
    if (not setting('features.fleets_enabled')):
        await ctx.send("That feature is not enabled.")
        return
    if (not ctx.invoked_subcommand):
        did = ctx.author.id
        fleet = userinfo.UserFleet.instance(1, did)
        if(len(fleet.ships) > 0):
            ins = fleet.get_ship_instances()
            fleet_lvl = sum(x.level for x in ins) // len(ins)

            embed = discord.Embed(title=namesub("%s's <fleet.title>") % str(ctx.author))
            embed.color = 524358
            flag = ins.pop(0)
            embed.add_field(name=namesub('<ship.title>'), value=flag.base().stype + " "
                            + flag.base().name + " (*)\n" +
                            "\n".join([x.base().stype + " " + x.base().name
                                       for x in ins]), inline=True)
            ins.insert(0, flag)
            embed.add_field(name="Level", value="\n".join(
                [str(x.level) for x in ins]), inline=True)
            embed.add_field(name="ID", value="\n".join(
                ["%04d" % (x.invid) for x in ins]), inline=True)
            embed.set_footer(text=namesub("<fleet.title> level %d") % fleet_lvl)

            await ctx.send(embed=embed)
        else:
            await ctx.send(namesub("<fleet.title> %s is empty!" % (1)))


@fleet.command(help=namesub("Add a <ship.title> to a <fleet>"), name="add", usage=namesub("[<ship.title> ID]"),
               hidden=not setting('features.fleets_enabled'))
async def f_add(ctx, shipid: int):
    """Add a ship to the user's fleet."""
    if (not setting('features.fleets_enabled')):
        await ctx.send("That feature is not enabled.")
        return
    did = ctx.author.id
    fleet = userinfo.UserFleet.instance(1, did)
    inv = userinfo.get_user_inventory(did)
    ins = [x for x in inv.inventory if x.invid == shipid]
    if (len(ins) > 0):
        ins = ins.pop()
        if (shipid not in fleet.ships):
            if (not fleet.has_similar(ins.sid)):
                if (len(fleet.ships) < setting('fleets.fleet_capacity')):
                    fleet.ships.append(shipid)
                    fleet.update()
                    await ctx.send(namesub("Added %s to <fleet> %s\n\n%s: *%s*") % (
                        ins.base().name, 1, ins.base().name,
                        ins.base().get_quote('fleet_join')))
                else:
                    await ctx.send(namesub("<fleet.title> %s is full!" % (1)))
            else:
                await ctx.send(namesub("You already have another %s in <fleet> %s!")
                               % (ins.base().name, 1))
        else:
            await ctx.send(namesub("%s is already in <fleet> %s!") % (ins.base().name, 1))
    else:
        await ctx.send(namesub("<ship.title> with ID %s not found in your inventory") % (
            shipid))


@fleet.command(help=namesub("Set a <fleet> with up to %d <ship_plural>") % (setting('fleets.fleet_capacity')),
               name="set", usage=namesub("[<flagship.title>] (<ship.title>2) (<ship.title>3) ..."),
               hidden=not setting('features.fleets_enabled'))
async def f_set(ctx, *ships):
    """Set the user's fleet to the given ships."""
    if (not setting('features.fleets_enabled')):
        await ctx.send("That feature is not enabled.")
        return
    did = ctx.author.id
    fleet = userinfo.UserFleet.instance(1, did)
    inv = userinfo.get_user_inventory(did)
    sids_raw = map(int, ships)
    sids_raw = [x for x in sids_raw if x >
                0 and x in map(lambda n: n.invid, inv.inventory)]
    # check for no dupes while still keeping order
    sids = []
    for x in sids_raw:
        if x in sids:
            continue
        sid = [y for y in inv.inventory if y.invid == x].pop().sid
        if sid in map(lambda y: [z for z in inv.inventory if z.invid == y]
                      .pop().sid, sids):
            continue
        sids.append(x)
    if (len(sids) == 0):
        await ctx.send(namesub("Please include at least one valid <ship.title> ID"))
    elif(len(sids) > setting('fleets.fleet_capacity')):
        await ctx.send(namesub("Too many <ship_plural> in the <fleet>!"))
    else:
        fleet.ships = sids
        fleet.update()
        strs = fleet_strings(inv, fleet)
        flag = strs.pop(0)
        line_base = [x for x in inv.inventory if x.invid ==
                     sids[0]].pop().base()
        if (len(strs) > 0):
            await ctx.send(namesub("Set <fleet> %s to: <flagship.title> %s, <ship_plural> %s\n\n%s: *%s*")
                           % (1, flag, ", ".join(strs), line_base.name,
                              line_base.get_quote('fleet_join')))
        else:
            await ctx.send(namesub("Set <fleet> %s to: <flagship.title> %s\n\n%s: *%s*")
                           % (1, flag, line_base.name,
                              line_base.get_quote('fleet_join')))


@fleet.command(help=namesub("Set a <fleet>'s <flagship>"),
               name=setting('commands.fleet_flag'),
               usage=namesub("[<flagship.title>]"),
               hidden=not setting('features.fleets_enabled'))
async def f_flag(ctx, flagship: int):
    """Set the flagship for the user's fleet."""
    if (not setting('features.fleets_enabled')):
        await ctx.send("That feature is not enabled.")
        return
    did = ctx.author.id
    fleet = userinfo.UserFleet.instance(1, did)
    inv = userinfo.get_user_inventory(did)
    ins = [x for x in inv.inventory if x.invid == flagship]
    if (len(ins) > 0):
        ins = ins.pop()
        cancel = False
        if (len(fleet.ships) > 0):
            old_flag = fleet.ships.pop(0)
            if (not old_flag == flagship):
                if (flagship in fleet.ships):
                    fleet.ships.remove(flagship)
                else:
                    if (len(fleet.ships) > setting('fleets.fleet_capacity')):
                        cancel = True
                        await ctx.send(namesub("<fleet.title> %s is full!") % (1))
                    if ins.sid in map(lambda x: [y for y in inv.inventory
                                                 if y.invid == x].pop().sid,
                                      fleet.ships):
                        cancel = True
                        await ctx.send(namesub("You already have another %s in <fleet> "
                                               "%s!") % (ins.base().name, 1))
                fleet.ships.append(old_flag)
            else:
                cancel = True
                await ctx.send(namesub("%s is already <flagship> of <fleet> %s!") % (
                    ins.base().name, 1))
            fleet.ships.insert(0, flagship)
        else:
            fleet.ships = [flagship, ]
        if (not cancel):
            fleet.update()
            await ctx.send(namesub("Set %s as the <flagship> of <fleet> %s\n\n%s: *%s*") % (
                ins.base().name, 1, ins.base().name,
                ins.base().get_quote('fleet_join')))
    else:
        await ctx.send(namesub("<ship.title> with ID %s not found in your inventory") % (
            flagship))


@fleet.command(help=namesub("Remove a <ship.title> from a <fleet>"), name="rem",
               usage=namesub("[<ship.title> ID]"), aliases=["remove"],
               hidden=not setting('features.fleets_enabled'))
async def f_rem(ctx, shipid: int):
    """Remove a ship from a user's fleet."""
    if (not setting('features.fleets_enabled')):
        await ctx.send("That feature is not enabled.")
        return
    did = ctx.author.id
    fleet = userinfo.UserFleet.instance(1, did)
    inv = userinfo.get_user_inventory(did)
    ins = [x for x in inv.inventory if x.invid == shipid]
    if (len(ins) > 0):
        ins = ins.pop()
        base = ins.base()
        if (shipid in fleet.ships):
            fleet.ships.remove(shipid)
            fleet.update()
            await ctx.send(namesub("Removed %s from <fleet> %s!") % (base.name, 1))
        else:
            await ctx.send(namesub("%s isn't in <fleet> %s!") % (base.name, 1))
    else:
        await ctx.send(namesub("<ship.title> with ID %s not found in your inventory") % (
            shipid))


@fleet.command(help=namesub("Clear a <fleet>"), name="clear",
               hidden=not setting('features.fleets_enabled'))
async def f_clear(ctx):
    """Clear a user's fleet."""
    if (not setting('features.fleets_enabled')):
        await ctx.send("That feature is not enabled.")
        return
    did = ctx.author.id
    fleet = userinfo.UserFleet.instance(1, did)
    fleet.ships = []
    fleet.update()
    await ctx.send(namesub("Cleared <fleet> %s!") % (1))


@bot.event
async def on_ready():
    """Run when the bot initializes fully."""
    print("Ready on {} ({})".format(bot.user.name, bot.user.id))
    logging.info("Loading ships...")
    ship_stats.get_all_ships()  # add ships to cache
    logging.info("Ships loaded")

BONUS_COOLDOWN = 120


@bot.event
async def on_message(message):
    """Run when a user sends a message that the bot can see."""
    if (not message.author.bot):
        did = message.author.id

        if (isinstance(message.channel, discord.DMChannel)):
            targ_server = 245830822580453376
            targ_channel = 446559630315749376
            chnl = bot.get_guild(targ_server).get_channel(targ_channel)
            msg = "%s#%s: %s" % (message.author.name,
                                 message.author.discriminator, message.content)
            await chnl.send(msg)
            logging.info("[PM] %s" % msg)
        elif (userinfo.check_cooldown(did, 'Last_Bonus', BONUS_COOLDOWN) == 0):
            user = userinfo.get_user(did)
            user.mod_fuel(setting_random('resources.passive_gain.fuel'))
            user.mod_ammo(setting_random('resources.passive_gain.ammo'))
            user.mod_steel(setting_random('resources.passive_gain.steel'))
            user.mod_bauxite(setting_random('resources.passive_gain.bauxite'))

            fleet = userinfo.UserFleet.instance(1, did)
            if (setting('features.levels_enabled') and len(fleet.ships) > 0):
                si_flag = fleet.get_ship_instances()[0]
                flag_exp = setting_random('levels.passive_flag_bonus')
                lvl = si_flag.add_exp(flag_exp)
                if (lvl):
                    await message.channel.send("**%s** - *%s* has leveled up! "
                                               "(Level %s!)"
                                               % (message.author.display_name,
                                                   si_flag.base().name,
                                                   si_flag.level))

    await bot.process_commands(message)


async def birthday_task():
    """Handle the kanmusu birthday channel(s)."""
    await bot.wait_until_ready()
    channels = []
    current_time = datetime.datetime.now(tz=datetime.timezone.utc)
    day = current_time.day
    mon = current_time.month
    with open(os.path.join(DIR_PATH, "../birthdays.json"), 'r') as jd:
        bdays = json.load(jd)
    clist = bdays['_send_channels']
    for c in clist:
        channels.append(bot.get_channel(int(c)))
    logging.info("Starting birthday task, current date is %s/%s" % (day, mon))
    startup_send = False
    while not bot.is_closed():
        current_time = datetime.datetime.now(tz=datetime.timezone.utc)
        cur_day = current_time.day
        cur_mon = current_time.month
        if (cur_day != day or cur_mon != mon or startup_send):
            startup_send = False
            logging.info("Time changed, setting stored to %s/%s" %
                         (cur_day, cur_mon))
            day = cur_day
            mon = cur_mon

            ship_names = []
            look = "%02d-%02d" % (day, mon)
            for k, v in bdays.items():
                if (v == look):
                    ship_names.append(k)
            if (len(ship_names) > 0):
                ships = ship_stats.get_all_ships(allow_remodel=False)
                msg = "Happy birthday, %s!"
                for sn in ship_names:
                    for sb in ships:
                        if (sb.name.lower() == sn.lower()):
                            bio = imggen.get_birthday_image(sb)
                            file = discord.File(io.BytesIO(
                                bio.getvalue()), filename="image.png")
                            for c in channels:
                                await c.send(file=file, content=(
                                    msg % sb.name))
            else:
                msg = "There are no birthdays today. (%02d/%02d)" % (day, mon)
                for c in channels:
                    await c.send(content=msg)
        await asyncio.sleep(30)


async def backup_task():
    """Automatically back up the user database."""
    await bot.wait_until_ready()
    if (not setting('backups.enabled')):
        logging.info("Backups not enabled, stopping task...")
        return
    DIR_PATH = os.path.dirname(os.path.realpath(__file__))
    DB_PATH = os.path.join(DIR_PATH, "../usersdb.db")  # hidden to git
    BACKUP_DIR = os.path.join(DIR_PATH, setting('backups.backup_folder_local'))
    await asyncio.sleep(20)
    while not bot.is_closed():
        now = datetime.datetime.now()
        backup_name = "usersdb-backup-%s.db" % (
            now.strftime("%y-%m-%d.%H-%M-%S"))
        backup_file = os.path.join(BACKUP_DIR, backup_name)
        backup_file = str(os.path.realpath(backup_file)).replace('\\', '\\\\')
        db_loc = str(os.path.realpath(DB_PATH))
        logging.info("Creating backup %s..." % backup_file)
        subprocess.check_output(
            ['sqlite3', db_loc, '.backup %s' % backup_file])
        await asyncio.sleep(setting('backups.backup_time'))


@bot.event
async def on_command_error(ctx, err):
    """Run when an error is handled after a user runs a faulty command."""
    await ctx.send("Error: %s" % str(err))
    traceback.print_exception(
        type(err), err, err.__traceback__, file=sys.stderr)


@bot.event
async def on_command(ctx):
    """Run when a user types any command."""
    logging.info("[Command] %s (%s) executed a command: %s" %
                 (str(ctx.author), ctx.author.id, ctx.message.content))

if __name__ == '__main__':
    DIR_PATH = os.path.dirname(os.path.realpath(__file__))
    logpath = os.path.realpath(os.path.join(DIR_PATH, '../output.log'))
    logging.basicConfig(
        filename=logpath, format='[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)
    logging.info("Starting bot...")
    with open(os.path.join(DIR_PATH, "../botinfo.json"), 'r') as bi:
        info = json.load(bi)
        key = info['key']  # yeah, no, I'm keeping this secret
    logging.info("Creating async tasks...")
    bot.loop.create_task(birthday_task())
    bot.loop.create_task(backup_task())
    logging.info("Running bot...")
    bot.run(key)
