import discord
from discord.ext import commands
import asyncio
import imggen
import io
import drophandler
import craftinghandler
import userinfo
import os
import random
import traceback
import sys
import fleet_training
import sorties
import ship_stats
import json
import datetime

COMMAND_PREFIX = "bg!"

bot = commands.Bot(command_prefix=COMMAND_PREFIX)

DROP_COOLDOWN = 4 * 60 * 60
CRAFTING_COOLDOWN = 15 * 60
TRAINING_COOLDOWN = 60 * 60

@bot.command(help="Show a ship from your inventory", usage="[Ship ID]")
async def show(ctx, shipid: int):
    did = ctx.author.id
    inv = userinfo.get_user_inventory(did)
    ins = [x for x in inv.inventory if x.invid == shipid]
    if (len(ins) > 0):
        ship_instance = ins.pop()
        base = ship_instance.base()
        image_file = imggen.generate_ship_card(ctx.bot, ship_instance)
        quotes_check = []
        if (ship_instance.level >= 100):
            quotes_check.append('Married')
        quotes_check.extend(['Idle', 'Poke(1)', 'Poke(2)', 'Poke(3)'])
        for q in quotes_check:
            quote = base.get_quote(q)
            if (quote != '???'):
                break
        await ctx.send(file=discord.File(io.BytesIO(image_file.getvalue()), filename="image.png"), content="%s: *%s*" % (base.name, quote))
    else:
        await ctx.send("Ship with ID %s not found in your inventory" % (shipid))

@bot.command(help="Get a random ship drop, cooldown of 4h")
async def drop(ctx):
    did = ctx.author.id
    if (userinfo.has_space_in_inventory(did)):
        cd = userinfo.check_cooldown(did, 'Last_Drop', DROP_COOLDOWN)
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
                    filename="image.png"), content="%s got %s! (%s)\n\n%s: *%s*" % (ctx.author.display_name, ship_name, rarity[ship_rarity - 1], ship_name, ship_base.get_quote('Intro')))
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
        cd = userinfo.check_cooldown(did, 'Last_Craft', CRAFTING_COOLDOWN, set_if_off=False)
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
                    userinfo.check_cooldown(did, 'Last_Craft', CRAFTING_COOLDOWN, set_if_off=True) # set cooldown
                    image_file = imggen.generate_ship_card(ctx.bot, craft)
                    ship_base = craft.base()
                    await ctx.send(file=discord.File(io.BytesIO(image_file.getvalue()),
                            filename="image.png"), content="%s just crafted %s!\n\n%s: *%s*" % (ctx.author.display_name, ship_base.name, ship_base.name, ship_base.get_quote('Intro')))
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
                ship_instance.sid = base.remodels_into
                base = ship_instance.base()
                new_name = base.name
                userinfo.update_ship_sid(ship_instance)
                image_file = imggen.generate_ship_card(ctx.bot, ship_instance)
                await ctx.send(file=discord.File(io.BytesIO(image_file.getvalue()), filename="image.png"), content="%s: *%s*" % (new_name, base.get_quote('Equip(3)')))
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
                        cd = userinfo.check_cooldown(did, "Last_Training", TRAINING_COOLDOWN)
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


@bot.command(help="Show your active cooldowns", aliases=["cd"])
async def cooldowns(ctx):
    did = ctx.author.id
    cd_check = [("Last_Drop", "Drop", DROP_COOLDOWN),
                ("Last_Training", "Fleet Training", TRAINING_COOLDOWN),
                ("Last_Craft", "Crafting", CRAFTING_COOLDOWN),
                ]
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

@bot.command(help="Using a Ring, marry a max level ship to increase their level cap", aliases=["ring"])
async def marry(ctx, shipid: int):
    did = ctx.author.id
    user = userinfo.get_user(did)
    inv = userinfo.get_user_inventory(did)
    ins = [x for x in inv.inventory if x.invid == shipid]
    if (len(ins) > 0):
        ship_instance = ins.pop()
        base = ship_instance.base()
        if (ship_instance.level == 99):
            rings = user.rings
            if (rings > 0):
                ship_instance.level = 100
                ship_instance.exp = 0
                ship_instance.add_exp(0)
                user.use_ring()
                ship_name = base.name
                image_file = imggen.generate_ship_card(ctx.bot, ship_instance)
                await ctx.send(file=discord.File(io.BytesIO(image_file.getvalue()), filename="image.png"),
                               content="%s: *%s*" % (ship_name, base.get_quote('Wedding')))
            else:
                await ctx.send("You don't have any more rings.")
        else:
            await ctx.send("%s isn't ready for marriage yet." % (base.name))
    else:
        await ctx.send("Ship with ID %s not found in your inventory" % (shipid))

@bot.command(help="Show the sortie map")
@commands.is_owner()
async def newmap(ctx):
    sortie = sorties.random_sortie()
    image_file = imggen.generate_sortie_card(sortie)
    await ctx.send(file=discord.File(io.BytesIO(image_file.getvalue()), filename="image.png"))

def fleet_strings(inv, fleet_s):
    ship_ins = list(map(lambda x: [y for y in inv.inventory if y.invid == x].pop(), fleet_s.ships))
    ship_data = list(map(lambda x: "*%s* (L%02d, %s)" % (x.base().name, x.level, x.base().stype), ship_ins))
    return ship_data

@bot.group(help="View your fleet (Subcommands for fleet management)")
async def fleet(ctx):
    if (not ctx.invoked_subcommand):
        did = ctx.author.id
        fleet = userinfo.UserFleet.instance(1, did)
        inv = userinfo.get_user_inventory(did)
        if(len(fleet.ships) > 0):
            strs = fleet_strings(inv, fleet)
            ins = fleet.get_ship_instances()
            fleet_lvl = sum(x.level for x in ins) // len(ins)
            flag = strs.pop(0)
            if (len(strs) > 0):
                await ctx.send("Fleet %s: Flagship %s, ships %s [Fleet Level %s]" % (1, flag, ", ".join(strs), fleet_lvl))
            else:
                await ctx.send("Fleet %s: Flagship %s [Fleet Level %s]" % (1, flag, fleet_lvl))
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
                    await ctx.send("Added %s to fleet %s\n\n%s: *%s*" % (ins.base().name, 1, ins.base().name, ins.base().get_quote('Join')))
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
        line_base = [x for x in inv.inventory if x.invid == sids[0]].pop().base()
        if (len(strs) > 0):
            await ctx.send("Set fleet %s to: Flagship %s, ships %s\n\n%s: *%s*" % (1, flag, ", ".join(strs), line_base.name, line_base.get_quote('Join')))
        else:
            await ctx.send("Set fleet %s to: Flagship %s\n\n%s: *%s*" % (1, flag, line_base.name, line_base.get_quote('Join')))

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
            await ctx.send("Set %s as the flagship of fleet %s\n\n%s: *%s*" % (ins.base().name, 1, ins.base().name, ins.base().get_quote('Join')))
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
    print("Loading ships...")
    ship_stats.get_all_ships() # add ships to cache
    print("Done!")

BONUS_COOLDOWN = 60

@bot.event
async def on_message(message):
    if (not message.author.bot):
        did = message.author.id
        if (userinfo.check_cooldown(did, 'Last_Bonus', BONUS_COOLDOWN) == 0):
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

        if (isinstance(message.channel, discord.DMChannel)):
            targ_server = 245830822580453376
            targ_channel = 446559630315749376
            chnl = bot.get_guild(targ_server).get_channel(targ_channel)
            await chnl.send("%s#%s: %s" % (message.author.name, message.author.discriminator, message.content))
    await bot.process_commands(message)

async def birthday_task():
    await bot.wait_until_ready()
    channels = []
    current_time = datetime.datetime.now(tz=datetime.timezone.utc)
    day = current_time.minute
    mon = current_time.hour
    with open(os.path.join(DIR_PATH, "birthdays.json"), 'r') as jd:
        bdays = json.load(jd)
    clist = bdays['_send_channels']
    for c in clist:
        channels.append(bot.get_channel(int(c)))
    print ("Starting task, current date is %s/%s" % (day, mon))
    startup_send = False
    while not bot.is_closed():
        current_time = datetime.datetime.now(tz=datetime.timezone.utc)
        cur_day = current_time.day
        cur_mon = current_time.month
        if (cur_day != day or cur_mon != mon or startup_send):
            startup_send = False
            print("Time changed, setting stored to %s/%s" % (cur_day, cur_mon))
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
                            file = discord.File(io.BytesIO(bio.getvalue()), filename="image.png")
                            for c in channels:
                                await c.send(file=file, content=(msg % sb.name))
            else:
                msg = "There are no birthdays today. (%s/%s)" % (day, mon)
                for c in channels:
                    await c.send(content=msg)
        await asyncio.sleep(10)


@bot.event
async def on_command_error(ctx, err):
    await ctx.send("Error: %s" % str(err))
    traceback.print_exception(type(err), err, err.__traceback__, file=sys.stderr)

if __name__ == '__main__':
    DIR_PATH = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(DIR_PATH, "botinfo.json"), 'r') as bi:
        info = json.load(bi)
        key = info['key'] # yeah, no, I'm keeping this secret
    bot.loop.create_task(birthday_task())
    bot.run(key)
