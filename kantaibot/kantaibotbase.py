import discord
from discord.ext import commands
import asyncio
import imggen
import ship_stats
import io
import drophandler
import userinfo
import os

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
        raise commands.UserInputError("Ship with ID %s not found in your inventory" % (shipid))

@bot.command(help="Get a random ship drop")
async def drop(ctx):
    did = ctx.author.id
    drop = drophandler.get_random_drop(did)
    image_file = imggen.generate_ship_card(ctx.bot, drop)
    ship_base = drop.base()
    ship_name = ship_base.name
    ship_rarity = ship_base.rarity
    rarity = ['Common', 'Common', 'Common', 'Uncommon', 'Rare', 'Very Rare', 'Extremely Rare', '**Legendary**']
    inv = userinfo.get_user_inventory(ctx.author.id)
    inv.add_to_inventory(drop)

    await ctx.send(file=discord.File(io.BytesIO(image_file.getvalue()),
            filename="image.png"), content="%s got a%s %s! (%s)" % (ctx.author.display_name, 'n' if ship_name[0].lower() in 'aeiou' else '', ship_name, rarity[ship_rarity - 1]))

@bot.command(help="Show your inventory", usage="(Page #)")
async def inv(ctx, page: int=1):
    did = ctx.author.id
    image_file = imggen.generate_inventory_screen(ctx.author, page)
    await ctx.send(file=discord.File(io.BytesIO(image_file.getvalue()), filename="image.png"), content=ctx.author.mention)


@bot.event
async def on_ready():
    print("Ready on {} ({})".format(bot.user.name, bot.user.id))
    await bot.change_presence(activity=discord.Game(type=0, name='with cute ships'))
    print("Current drop chances (Rarity, Chance):")
    chances = drophandler.get_drop_chances()
    for r in range(8):
        print(" %s | %.04f" % (r + 1, chances[r]))


@bot.event
async def on_command_error(ctx, err):
    await ctx.send("Error: %s" % str(err))


if __name__ == '__main__':
    DIR_PATH = os.path.dirname(os.path.realpath(__file__))
    f = open(os.path.join(DIR_PATH, "botinfo.txt") , 'r')
    key = f.readline()[:-1] # yeah, no, I'm keeping this secret
    bot.run(key)
