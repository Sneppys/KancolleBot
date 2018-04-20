import discord
from discord.ext import commands
import asyncio
import imggen
import ship_stats
import io
import drophandler
import craftinghandler
import userinfo
import os
import random
import traceback
import sys
import fleet_training

COMMAND_PREFIX = "bg!"

bot = commands.Bot(command_prefix=COMMAND_PREFIX)

@bot.command(help="Show a ship from your inventory", usage="[Ship ID]")
async def show(ctx, shipid: int):
    did = ctx.author.id
    inv = userinfo.get_user_inventory(did)
    ins = [x for x in inv.inventory if x.invid == shipid]
    if (len(ins) > 0):
        ship_instance = ins.pop()
        image_file = imggen.generate_ship_card(ctx.bot, ship_instance)
        await ctx.send(file=discord.File(io.BytesIO(image_file.getvalue()), filename="image.png"))
    else:
        await ctx.send("Ship with ID %s not found in your inventory" % (shipid))

@bot.command(help="Get a random ship drop, cooldown of 4h")
async def drop(ctx):
    did = ctx.author.id
    if (userinfo.has_space_in_inventory(did)):
        cd = userinfo.check_cooldown(did, 'Last_Drop', 4 * 3600)
        if (cd == 0):
            drop = drophandler.get_random_drop(did, only_droppable=True)
            image_file = imggen.generate_ship_card(ctx.bot, drop)
            ship_base = drop.base()
            ship_name = ship_base.name
            ship_rarity = ship_base.rarity
            rarity = ['Common', 'Common', 'Common', 'Uncommon', 'Rare', 'Very Rare', 'Extremely Rare', '**Legendary**']
            inv = userinfo.get_user_inventory(did)
            inv.add_to_inventory(drop)

            await ctx.send(file=discord.File(io.BytesIO(image_file.getvalue()),
                    filename="image.png"), content="%s got a%s %s! (%s)" % (ctx.author.display_name, 'n' if ship_name[0].lower() in 'aeiou' else '', ship_name, rarity[ship_rarity - 1]))
        else:
            hrs = cd // 3600
            min = cd // 60 % 60
            sec = cd % 60
            await ctx.send("You have %dh%02dm%02ds remaining until you can get your next drop" % (hrs, min, sec))
    else:
        await ctx.send("Your inventory is full! You can scrap a ship with `%sscrap [Ship ID]`" % COMMAND_PREFIX)

@bot.command(help="Show your inventory", usage="(Page #)")
async def inv(ctx, page: int=1):
    did = ctx.author.id
    image_file = imggen.generate_inventory_screen(ctx.author, page)
    await ctx.send(file=discord.File(io.BytesIO(image_file.getvalue()), filename="image.png"))

@bot.command(help="Craft a ship with the given resources, 15min cooldown", usage="[Fuel] [Ammo] [Steel] [Bauxite]")
async def craft(ctx, fuel: int, ammo: int, steel: int, bauxite: int):
    did = ctx.author.id
    user = userinfo.get_user(did)
    if (userinfo.has_space_in_inventory(did)):
        cd = userinfo.check_cooldown(did, 'Last_Craft', 15 * 60, set_if_off=False)
        if (cd == 0):
            if (fuel >= 30 and ammo >= 30 and steel >= 30 and bauxite >= 30):
                if (user.has_enough(fuel, ammo, steel, bauxite)):
                    craft = craftinghandler.get_craft_from_resources(did, fuel, ammo, steel, bauxite)
                    user.mod_fuel(-fuel)
                    user.mod_ammo(-ammo)
                    user.mod_steel(-steel)
                    user.mod_bauxite(-bauxite)
                    inv = userinfo.get_user_inventory(did)
                    inv.add_to_inventory(craft)
                    userinfo.check_cooldown(did, 'Last_Craft', 15 * 60, set_if_off=True) # set cooldown
                    image_file = imggen.generate_ship_card(ctx.bot, craft)
                    ship_base = craft.base()
                    await ctx.send(file=discord.File(io.BytesIO(image_file.getvalue()),
                            filename="image.png"), content="%s just crafted %s!" % (ctx.author.display_name, ship_base.name))
                else:
                    await ctx.send("Not enough resources!")
            else:
                await ctx.send("Use at least 30 of each resource")
        else:
            min = cd // 60
            sec = cd % 60
            await ctx.send("You have %dm%02ds remaining until you can craft another ship" % (min, sec))
    else:
        await ctx.send("Your inventory is full! You can scrap a ship with `%sscrap [Ship ID]`" % COMMAND_PREFIX)

@bot.command(help="Scraps a ship, removing it for a tiny amount of resources", usage="[Ship ID]")
async def scrap(ctx, shipid: int):
    did = ctx.author.id
    user = userinfo.get_user(did)
    inv = userinfo.get_user_inventory(did)
    ins = [x for x in inv.inventory if x.invid == shipid]
    if (len(ins) > 0):
        ship_instance = ins.pop()
        base = ship_instance.base()
        # MAYBE: change award amount based on ship type
        user.mod_fuel(random.randrange(8) + 5)
        user.mod_ammo(random.randrange(8) + 5)
        user.mod_steel(random.randrange(10) + 7)
        user.mod_bauxite(random.randrange(5) + 3)
        inv.remove_from_inventory(shipid)
        await ctx.send("Scrapped %s... <:roosad:434916104268152853>" % base.name)
    else:
        await ctx.send("Ship with ID %s not found in your inventory" % (shipid))

@bot.command(help="Shows your inventory, hiding all ships except duplicates", usage="(Page #)")
async def dupes(ctx, page: int=1):
    did = ctx.author.id
    image_file = imggen.generate_inventory_screen(ctx.author, page, only_dupes=True)
    await ctx.send(file=discord.File(io.BytesIO(image_file.getvalue()), filename="image.png"))

@bot.command(help="Remodel a ship if it is a high enough level", usage="[Ship ID]")
async def remodel(ctx, shipid: int):
    did = ctx.author.id
    user = userinfo.get_user(did)
    inv = userinfo.get_user_inventory(did)
    ins = [x for x in inv.inventory if x.invid == shipid]
    if (len(ins) > 0):
        ship_instance = ins.pop()
        base = ship_instance.base()
        if (base.remodels_into):
            if (ship_instance.is_remodel_ready()):
                old_name = base.name
                ship_instance.sid = base.remodels_into
                new_name = ship_instance.base().name
                userinfo.update_ship_sid(ship_instance)
                image_file = imggen.generate_ship_card(ctx.bot, ship_instance)
                await ctx.send(file=discord.File(io.BytesIO(image_file.getvalue()), filename="image.png"), content="*%s* is now *%s!*" % (old_name, new_name))
            else:
                await ctx.send("%s isn't ready for a remodel just yet." % (base.name))
        else:
            await ctx.send("%s doesn't have another remodel." % (base.name))
    else:
        await ctx.send("Ship with ID %s not found in your inventory" % (shipid))

@bot.command(help="Show all training difficulties or train a fleet on one", usage="(Difficulty #)")
async def train(ctx, dif: int=-1):
    did = ctx.author.id
    difs = fleet_training.ALL_DIFFICULTIES
    if (dif == -1):
        description = "Difficulties:\n"
        description += "\n".join(["#%s. %s: Min Flagship level %s, Recommended fleet level %s." % (x + 1,
                        difs[x].name, difs[x].min_flag, difs[x].avg_lvl) for x in range(len(difs))])
        footer = "Type %strain (#) to train a fleet with a difficulty" % (COMMAND_PREFIX)
        embed = discord.Embed(title="Fleet Training", description=description)
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
                        cd = userinfo.check_cooldown(did, "Last_Training", 2 * 3600)
                        if (cd == 0):
                            # conditions passed
                            rank = dif_targ.rank_training(fleet)

                            exp_rew_base = rank.exp_mult * dif_targ.exp_reward_base
                            exp_rew_split = rank.exp_mult * dif_targ.exp_reward_split

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

                            embed = discord.Embed(title="Training %s" % ("Success" if rank.is_success else "Failed"))
                            embed.color = 65280 if rank.is_success else 16711680
                            embed.description = "Rank %s | %s Difficulty" % (rank.symbol, dif_targ.name)
                            flag = ins.pop(0)
                            embed.add_field(name="EXP Gain", value=flag.base().name + " (*)\n" + "\n".join([x.base().name for x in ins]), inline=True)
                            embed.add_field(name="--------", value="\n".join(["+%g EXP" % x for x in exp]))
                            ins.insert(0, flag)
                            embed.add_field(name="--------", value="\n".join(["Level %s (+%s)" % (ins[i].level, lvl_dif[i]) for i in range(len(ins))]))
                            embed.set_footer(text="Used %g fuel, %g ammo, %g steel, %g bauxite" % rsc)

                            await ctx.send(embed=embed)
                        else:
                            hrs = cd // 3600
                            min = cd // 60 % 60
                            sec = cd % 60
                            await ctx.send("You have %dh%02dm%02ds remaining until you can train your fleet again" % (hrs, min, sec))
                    else:
                        await ctx.send("Not enough resources! (Required: %g fuel, %g ammo, %g steel, %g bauxite)" % rsc)
                else:
                    await ctx.send("Flagship isn't a high enough level! (Needs to be at least %s)" % (dif_targ.min_flag))
            else:
                await ctx.send("Fleet %s is empty!" % (1))
        else:
            await ctx.send("No such difficulty #%s" % dif)


def fleet_strings(inv, fleet):
    ship_ins = list(map(lambda x: [y for y in inv.inventory if y.invid == x].pop(), fleet.ships))
    ship_data = list(map(lambda x: "*%s* (L%02d, %s)" % (x.base().name, x.level, ship_stats.get_ship_type(x.base().shiptype).discriminator), ship_ins))
    return ship_data

@bot.group(help="View your fleet (Subcommands for fleet management)")
async def fleet(ctx):
    if (not ctx.invoked_subcommand):
        did = ctx.author.id
        fleet = userinfo.UserFleet.instance(1, did)
        inv = userinfo.get_user_inventory(did)
        if(len(fleet.ships) > 0):
            strs = fleet_strings(inv, fleet)
            flag = strs.pop(0)
            if (len(strs) > 0):
                await ctx.send("Fleet %s: Flagship %s, ships %s" % (1, flag, ", ".join(strs)))
            else:
                await ctx.send("Fleet %s: Flagship %s" % (1, flag))
        else:
            await ctx.send("Fleet %s is empty!" % (1))

@fleet.command(help="Add a ship to a fleet", name="add", usage="[Ship ID]")
async def f_add(ctx, shipid: int):
    did = ctx.author.id
    fleet = userinfo.UserFleet.instance(1, did)
    inv = userinfo.get_user_inventory(did)
    ins = [x for x in inv.inventory if x.invid == shipid]
    if (len(ins) > 0):
        ins = ins.pop()
        if (not shipid in fleet.ships):
            if (not fleet.has_similar(ins.sid)):
                if (len(fleet.ships) < 6):
                    fleet.ships.append(shipid)
                    fleet.update()
                    await ctx.send("Added %s to fleet %s" % (ins.base().name, 1))
                else:
                    await ctx.send("Fleet %s is full!" % (1))
            else:
                await ctx.send("You already have another %s in fleet %s!" % (ins.base().name, 1))
        else:
            await ctx.send("%s is already in fleet %s!" % (ins.base().name, 1))
    else:
        await ctx.send("Ship with ID %s not found in your inventory" % (shipid))

@fleet.command(help="Set a fleet with up to 6 ships", name="set",
               usage="[Flagship] (Ship2) (Ship3) ...")
async def f_set(ctx, flagship: int, ship2: int=-1, ship3: int=-1, ship4: int=-1,
                ship5: int=-1, ship6: int=-1):
    did = ctx.author.id
    fleet = userinfo.UserFleet.instance(1, did)
    inv = userinfo.get_user_inventory(did)
    sids_raw = [flagship, ship2, ship3, ship4, ship5, ship6]
    sids_raw = [x for x in sids_raw if x > 0 and x in map(lambda n: n.invid, inv.inventory)]
    # check for no dupes while still keeping order
    sids = []
    for x in sids_raw:
        if x in sids:
            continue
        sid = [y for y in inv.inventory if y.invid == x].pop().sid
        if sid in map(lambda y: [z for z in inv.inventory if z.invid == y].pop().sid, sids):
            continue
        sids.append(x)
    if (len(sids) == 0):
        await ctx.send("Please include at least one valid ship ID")
    else:
        fleet.ships = sids
        fleet.update()
        strs = fleet_strings(inv, fleet)
        flag = strs.pop(0)
        if (len(strs) > 0):
            await ctx.send("Set fleet %s to: Flagship %s, ships %s" % (1, flag, ", ".join(strs)))
        else:
            await ctx.send("Set fleet %s to: Flagship %s" % (1, flag))

@fleet.command(help="Set a fleet's flagship", name="flag", usage="[Flagship]", aliases=["flagship"])
async def f_flag(ctx, flagship: int):
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
                    if (len(fleet.ships) >= 5):
                        cancel = True
                        await ctx.send("Fleet %s is full!" % (1))
                    if ins.sid in map(lambda x: [y for y in inv.inventory if y.invid == x].pop().sid, fleet.ships):
                        cancel = True
                        await ctx.send("You already have another %s in fleet %s!" % (ins.base().name, 1))
                fleet.ships.append(old_flag)
            else:
                cancel = True
                await ctx.send("%s is already flagship of fleet %s!" % (ins.base().name, 1))
            fleet.ships.insert(0, flagship)
        else:
            fleet.ships = [flagship,]
        if (not cancel):
            fleet.update()
            await ctx.send("Set %s as the flagship of fleet %s" % (ins.base().name, 1))
    else:
        await ctx.send("Ship with ID %s not found in your inventory" % (flagship))

@fleet.command(help="Remove a ship from a fleet", name="rem", usage="[Ship ID]", aliases=["remove"])
async def f_rem(ctx, shipid: int):
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
            await ctx.send("Removed %s from fleet %s!" % (base.name, 1))
        else:
            await ctx.send("%s isn't in fleet %s!" % (base.name, 1))
    else:
        await ctx.send("Ship with ID %s not found in your inventory" % (shipid))

@fleet.command(help="Clear a fleet", name="clear")
async def f_clear(ctx):
    did = ctx.author.id
    fleet = userinfo.UserFleet.instance(1, did)
    fleet.ships = []
    fleet.update()
    await ctx.send("Cleared fleet %s!" % (1))

@bot.event
async def on_ready():
    print("Ready on {} ({})".format(bot.user.name, bot.user.id))
    await bot.change_presence(activity=discord.Game(type=0, name='with cute ships | %shelp' % COMMAND_PREFIX))


DROP_COOLDOWN = 60

@bot.event
async def on_message(message):
    if (not message.author.bot):
        did = message.author.id
        if (userinfo.check_cooldown(did, 'Last_Bonus', DROP_COOLDOWN) == 0):
            user = userinfo.get_user(did)
            user.mod_fuel(random.randrange(30) + 30)
            user.mod_ammo(random.randrange(30) + 30)
            user.mod_steel(random.randrange(30) + 30)
            user.mod_bauxite(random.randrange(20) + 15)

            fleet = userinfo.UserFleet.instance(1, did)
            if (len(fleet.ships) > 0):
                si_flag = fleet.get_ship_instances()[0]
                flag_exp = random.randrange(20) + 40
                lvl = si_flag.add_exp(flag_exp)
                if (lvl):
                    await message.channel.send("**%s** - *%s* has leveled up! (Level %s!)" % (message.author.display_name, si_flag.base().name, si_flag.level))
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, err):
    await ctx.send("Error: %s" % str(err))
    traceback.print_exception(type(err), err, err.__traceback__, file=sys.stderr)

if __name__ == '__main__':
    DIR_PATH = os.path.dirname(os.path.realpath(__file__))
    f = open(os.path.join(DIR_PATH, "botinfo.txt") , 'r')
    key = f.readline()[:-1] # yeah, no, I'm keeping this secret
    bot.run(key)
