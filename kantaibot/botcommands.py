import discord
import asyncio

COMMAND_PREFIX = "bg!"

async def command_hello(client, message):
    await send_bot_reply(client, message, "Hi!")

commands = {
"hello": command_hello,
}


async def send_bot_reply(client, message, reply):
    await client.send_message(message.channel, reply)

async def handle_message(client, message):
    global commands
    cmd = message.content.split()[0]
    for c, m in commands.items():
        targ_cmd = COMMAND_PREFIX + c
        if (targ_cmd.lower() == cmd.lower()):
            await m(client, message)
            break
