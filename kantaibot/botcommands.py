import discord
import asyncio
import imggen
import ship_stats
import io
import drophandler
import userinfo

COMMAND_PREFIX = "bg!"

async def command_hello(client, message, args):
    await client.send_message(message.channel, "Hi!")

async def command_show(client, message, args):
    did = message.author.id
    if (len(args) > 0):
        shipid = args[0]
        if (shipid.isdigit()):
            shipid = int(shipid)
            inv = userinfo.get_user_inventory(did)
            ins = [x for x in inv.inventory if x.invid == shipid]
            if (len(ins) > 0):
                ship_instance = ins.pop()
                image_file = imggen.generate_ship_card(client, ship_instance)
                await client.send_file(message.channel, io.BytesIO(image_file.getvalue()), filename="image.png")
            else:
                await client.send_message(message.channel, "Ship with ID %s not found in your inventory" % (shipid))
        else:
            await client.send_message(message.channel, "Please type a valid number")
    else:
        await client.send_message(message.channel, "Usage: `%sshow [ship_id]`" % COMMAND_PREFIX)

async def command_drop(client, message, args):
    did = message.author.id
    drop = drophandler.get_random_drop(did)
    image_file = imggen.generate_ship_card(client, drop)
    ship_base = drop.base()
    ship_name = ship_base.name
    ship_rarity = ship_base.rarity
    rarity = ['Common', 'Common', 'Common', 'Uncommon', 'Rare', 'Very Rare', 'Extremely Rare', '**Legendary**']
    inv = userinfo.get_user_inventory(message.author.id)
    inv.add_to_inventory(drop)

    await client.send_file(message.channel, io.BytesIO(image_file.getvalue()),
            filename="image.png", content="%s got a%s %s! (%s)" % (message.author.display_name, 'n' if ship_name[0].lower() in 'aeiou' else '', ship_name, rarity[ship_rarity - 1]))

async def command_inv(client, message, args):
    did = message.author.id
    page = 1
    if (len(args) > 0):
        pg = args[0]
        if (pg.isdigit()):
            page = int(pg)
    image_file = imggen.generate_inventory_screen(client, did, page)
    await client.send_file(message.channel, io.BytesIO(image_file.getvalue()), filename="image.png", content=message.author.mention)

commands = {
"hello": command_hello,
"show": command_show,
"drop": command_drop,
"inv": command_inv,
}


async def handle_message(client, message):
    global commands
    if (message.author.bot or len(message.content) == 0):
        return
    words = message.content.split()
    cmd = words[0]
    if (len(words) > 1):
        args = words[1:]
    else:
        args = []
    for c, m in commands.items():
        targ_cmd = COMMAND_PREFIX + c
        if (targ_cmd.lower() == cmd.lower()):
            await m(client, message, args)
            break
