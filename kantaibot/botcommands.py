import discord
import asyncio
import imggen
import ship_stats
import io
import drophandler

COMMAND_PREFIX = "bg!"

async def command_hello(client, message, args):
    await client.send_message(message.channel, "Hi!")

async def command_show(client, message, args):
    if (len(args) > 0):
        shipid = args[0]
        if (shipid.isdigit()):
            shipid = int(shipid)
            ship_instance = ship_stats.ShipInstance.new(shipid)
            image_file = imggen.generate_ship_card(ship_instance)
            await client.send_file(message.channel, io.BytesIO(image_file.getvalue()), filename="image.png")
        else:
            await client.send_message(message.channel, "Please type a valid number")
    else:
        await client.send_message(message.channel, "Usage: `%sshow [ship_id]`" % COMMAND_PREFIX)

async def command_drop(client, message, args):
    drop = drophandler.get_random_drop()
    image_file = imggen.generate_ship_card(drop)
    ship_base = drop.base()
    ship_name = ship_base.name
    ship_rarity = ship_base.rarity
    rarity = ['Common', 'Common', 'Common', 'Uncommon', 'Rare', 'Very Rare', 'Extremely Rare', '**Legendary**']

    await client.send_file(message.channel, io.BytesIO(image_file.getvalue()),
            filename="image.png", content="%s got a%s %s! (%s)" % (message.author.display_name, 'n' if ship_name[0].lower() in 'aeiou' else '', ship_name, rarity[ship_rarity - 1]))

commands = {
"hello": command_hello,
"show": command_show,
"drop": command_drop,
}


async def handle_message(client, message):
    global commands
    if (len(message.content) == 0):
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
