import discord
import asyncio


client = discord.Client()


@client.event
async def on_ready():
    print("Ready on {} ({})".format(client.user.name, client.user.id))


@client.event
async def on_message(message):
    print(message.author, message.content)


f = open('botinfo.txt', 'r')
key = f.readline()[:-1] # yeah, no, I'm keeping this secret
client.run(key)
