import discord
import asyncio
import imggen
import ship_stats
import io

COMMAND_PREFIX = "bg!"

async def command_hello(client, message, args):
    await client.send_message(message.channel, "Hi!")

async def command_show(client, message, args):
    ship_instance = ship_stats.ShipInstance.new(2)
    image_file = imggen.generate_ship_card(ship_instance)
    await client.send_file(message.channel, io.BytesIO(image_file.getvalue()), filename="image.png")


commands = {
"hello": command_hello,
"show": command_show,
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
