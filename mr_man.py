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

reserves = {}
hardres = {}

own_msg = {}


def default_message(raid):
    return "----------------- Soft reserves for " + raid.upper() + " ---------------\n"\
                                               "Type !res <item>\n"


def google_fu(item, location):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5)\
                AppleWebKit/537.36 (KHTML, like Gecko) Cafari/537.36'}
    try:
        for url in search("site:classic.wowhead.com/item= " + location + " " + item, stop=1):
            r = requests.get(url, headers=headers)
            soup = BeautifulSoup(r.text, "html.parser")
            name = str(soup.title.string)
            retval = name[:name.find(" -")]
            if retval == "Warblade of the Hakkari":
                if "oh" in item.lower() or "off" in item.lower():
                    return "Warblade of the Hakkari (OH)"
                else:
                    return "Warblade of the Hakkari (MH)"
            return retval

    except HTTPError as err:
        if err.code == 429:
            print(err.headers)
        return "Google is sending me hate mail, gotta chill :("


def stringify(d, hd):
    retval = {}
    print(d)
    print(hd)
    counter = 0
    for user, item in d.items():
        counter = counter + 1
        if str(item) not in retval:
            retval[str(item)] = [user]
        else:
            retval[str(item)].append(user)

    return "Total amount of reservations: " + str(counter) + "\n\n" + "Hard reserved: " + str(hd).replace("set()", "")\
                .replace("\"", "'").replace("{'", "").replace("'}", "").replace("', '", ", ") + "\n\n" + \
             str(retval).replace("\"", "'").replace("'], '", "\n").replace("{", "").replace("}", "")\
                .replace("', '", ", ").replace("['", "").replace("']", "").replace("':", ":")[1:]


@client.event
async def on_ready():
    print(f'{client.user} sjukt redo')
    await client.change_presence(activity=discord.Game(name="Skynet simulator"))


@client.event
async def on_message(msg):
    channel = msg.channel
    if msg.content.startswith("!") and "soft-res" in channel.name:
        async with channel.typing():
            data_in = msg.content[1:]
            if data_in == "?":
                response = google_fu("test", "test")
                if "hate mail" in response:
                    await channel.send(response, delete_after=20)
                else:
                    await channel.send("We back", delete_after=20)

            elif data_in.startswith("res"):
                if channel.name.startswith("mc"):
                    full_name = "molten core"
                    abbrev = "mc"
                    raid_msg = own_msg[abbrev]
                    res_dict = reserves[abbrev]
                    hardres_dict = hardres[abbrev]
                elif channel.name.startswith("zg"):
                    full_name = "zul'gurub"
                    abbrev = "zg"
                    raid_msg = own_msg[abbrev]
                    res_dict = reserves[abbrev]
                    hardres_dict = hardres[abbrev]
                else:
                    return

                item = google_fu(data_in[data_in.find(" "):], full_name)
                if item is not None and "hate mail" in item:
                    print(item)
                    await channel.send(item, delete_after=20)
                    return
                if item not in hardres_dict:
                    res_dict[msg.author.mention] = [item]

                print(channel.name, data_in[data_in.find(" "):], msg.author.display_name, item)
                post = await channel.fetch_message(raid_msg)
                await post.edit(content=default_message(abbrev) + stringify(res_dict, hardres_dict))

            for role in msg.author.roles:
                if "Hjälte" in role.name:
                    if data_in.startswith("hardres"):
                        if channel.name.startswith("mc"):
                            full_name = "molten core"
                            abbrev = "mc"
                            raid_msg = own_msg[abbrev]
                            res_dict = reserves[abbrev]
                            hardres_dict = hardres[abbrev]
                        elif channel.name.startswith("zg"):
                            full_name = "zul'gurub"
                            abbrev = "zg"
                            raid_msg = own_msg[abbrev]
                            res_dict = reserves[abbrev]
                            hardres_dict = hardres[abbrev]
                        else:
                            return

                        item = google_fu(data_in[data_in.find(" "):], full_name)
                        if item in hardres_dict:
                            hardres_dict.remove(item)
                        else:
                            hardres_dict.add(item)
                        res_dict = {k:v for k,v in res_dict.items() if v[0] not in hardres_dict}
                        print(channel.name, data_in[data_in.find(" "):], msg.author.display_name, item)
                        post = await channel.fetch_message(raid_msg)
                        await post.edit(content=default_message(abbrev) + stringify(res_dict, hardres_dict))

                    elif data_in == "lock":
                        await channel.set_permissions(msg.author.roles[0], send_messages=False)
                    elif data_in == "unlock":
                        await channel.set_permissions(msg.author.roles[0], overwrite=None)

                    else:
                        """
                        Because of the continue-statement, this has to be an else-clause at the bottom to make sure
                        the other clauses are checked before an eventual continuation
                        """
                        if data_in == "mc":
                            abbrev = "mc"
                        elif data_in == "zg":
                            abbrev = "zg"
                        else:
                            continue

                        async for post in channel.history():
                            await post.delete()
                        await channel.send(default_message(data_in.upper()) + "No reserves")
                        own_msg[abbrev] = channel.last_message_id
                        await channel.last_message.pin()
                        await channel.last_message.delete()
                        hardres[abbrev] = set()
                        reserves[abbrev] = {}
                        return

            await msg.delete()


client.run(TOKEN)
