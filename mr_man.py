import os
import discord
from googlesearch import search
from dotenv import load_dotenv
import requests
from urllib.error import HTTPError
from bs4 import BeautifulSoup
import time

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

client = discord.Client()

reserves_mc = {}
reserves_zg = {}

mc_msg = 3
zg_msg = 2


def default_message(raid):
    return "----------------- Soft reserves for " + raid + " ---------------\n"\
                                               "Type !res <item>\n"


def google_fu(item, location):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5)\
                AppleWebKit/537.36 (KHTML, like Gecko) Cafari/537.36'}
    try:
        for url in search("site:classic.wowhead.com/item= " + location + " " + item, stop=1):
            r = requests.get(url, headers=headers)
            soup = BeautifulSoup(r.text, "html.parser")
            name = str(soup.title.string)
            return name[:name.find(" -")]
    except HTTPError as err:
        if err.code == 429:
            print(err.headers)
        return "Google is sending me hate mail, gotta chill :("


def stringify(d):
    retval = {}
    for user, items in d.items():
        for item in items:
            if str(item) not in retval:
                retval[str(item)] = [user]
            else:
                retval[str(item)].append(user)

    return str(retval).replace("\"", "'").replace("'], '", "\n").replace("{", "").replace("}", "").replace("', '", ", ")\
        .replace("['", "").replace("']", "").replace("':", ":")[1:]


@client.event
async def on_ready():
    print(f'{client.user} sjukt redo')
    await client.change_presence(activity=discord.Game(name="Skynet simulator"))


@client.event
async def on_message(msg):
    global mc_msg, zg_msg
    channel = msg.channel
    if msg.content.startswith("!"):
        async with channel.typing():
            data_in = msg.content[1:]
            if data_in == "?":
                response = google_fu("test", "test")
                if "hate mail" in response:
                    await channel.send(response, delete_after=20)
                else:
                    await channel.send("We back", delete_after=20)

            elif channel.name.startswith("mc"):
                if data_in.startswith("res"):
                    item = google_fu(data_in[data_in.find(" "):], "molten core")
                    if item is not None and "hate mail" in item:
                        print(item)
                        await channel.send(item, delete_after=20)
                        return
                    reserves_mc[msg.author.mention] = [item]
                    print(channel.name, data_in[data_in.find(" "):], msg.author.display_name, item)
                    post = await channel.fetch_message(mc_msg)
                    await post.edit(content=default_message("MC") + stringify(reserves_mc))

            elif channel.name.startswith("zg"):
                if data_in.startswith("res"):
                    item = google_fu(data_in[data_in.find(" "):], "zul'gurub")
                    if item is not None and "hate mail" in item:
                        print(item)
                        await channel.send(item, delete_after=20)
                        return
                    reserves_zg[msg.author.mention] = [item]
                    print(channel.name, data_in[data_in.find(" "):], msg.author.display_name, item)
                    post = await channel.fetch_message(zg_msg)
                    await post.edit(content=default_message("ZG") + stringify(reserves_zg))

            for role in msg.author.roles:
                if "Hjälte" in role.name:
                    if data_in == "mc":
                        async for post in channel.history():
                            await post.delete()
                        await channel.send(default_message(data_in.upper()) + "No reserves")
                        mc_msg = channel.last_message_id
                        await channel.last_message.pin()
                        await channel.last_message.delete()
                    elif data_in == "zg":
                        async for post in channel.history():
                            await post.delete()
                        await channel.send(default_message(data_in.upper()) + "No reserves")
                        zg_msg = channel.last_message_id
                        await channel.last_message.pin()
                        await channel.last_message.delete()
                    elif data_in == "lock":
                        await channel.set_permissions(msg.author.roles[0], send_messages=False)
                    elif data_in == "unlock":
                        await channel.set_permissions(msg.author.roles[0], overwrite=None)

            await msg.delete()


client.run(TOKEN)
