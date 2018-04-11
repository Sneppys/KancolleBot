import discord
import asyncio
import botcommands
import os


client = discord.Client()


@client.event
async def on_ready():
    print("Ready on {} ({})".format(client.user.name, client.user.id))
    await client.change_presence(game=discord.Game(type=0, name='with cute ships'))


@client.event
async def on_message(message):
    await botcommands.handle_message(client, message)


DIR_PATH = os.path.dirname(os.path.realpath(__file__))
f = open(os.path.join(DIR_PATH, "botinfo.txt") , 'r')
key = f.readline()[:-1] # yeah, no, I'm keeping this secret
client.run(key)
