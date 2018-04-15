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
            drop = drophandler.get_random_drop(did)
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
        cd = userinfo.check_cooldown(did, 'Last_Craft', 15 * 60)
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

@bot.event
async def on_ready():
    print("Ready on {} ({})".format(bot.user.name, bot.user.id))
    await bot.change_presence(activity=discord.Game(type=0, name='with cute ships'))


@bot.event
async def on_message(message):
    if (not message.author.bot):
        drophandler.drop_resources(message.author.id)
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, err):
    await ctx.send("Error: %s" % str(err))


if __name__ == '__main__':
    DIR_PATH = os.path.dirname(os.path.realpath(__file__))
    f = open(os.path.join(DIR_PATH, "botinfo.txt") , 'r')
    key = f.readline()[:-1] # yeah, no, I'm keeping this secret
    bot.run(key)
