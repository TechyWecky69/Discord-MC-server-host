import os
import discord
from discord.ext import commands
from discord import app_commands
from discord.utils import get
from typing import Literal, Optional
import json
import functions
import string
import time
from dotenv import load_dotenv
import asyncio
import serverHandler
from functions import send_webhook

default_json = """
{
  "server":{}
}
"""

banned_words = [
    "FUCK", "SHIT", "WANK", "CUNT", "NIGGER", "NIGGA", "NIGER", "NIGA", "COCK",
    "DICK", "PISS", "SEX"
]

intents = discord.Intents.default()
intents.message_content = True

mod_roles = ["Owner", "Admin", "Helper"]

load_dotenv()

TOKEN = os.getenv("TOKEN")

bot = commands.Bot(intents=intents, command_prefix="!")


@bot.event
async def on_ready():
    print(f"Logged into {bot.user}")
    try:
        sync = await bot.tree.sync()
        print(f"Synced {len(sync)} command(s)")
    except Exception as e:
        print(e)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    for word in banned_words:
        if word in message.content.upper():
            await message.delete()
            warning_message = await message.channel.send(
                f"{message.author.mention}, you cannot say that!")
            time.sleep(5)
            await warning_message.delete()
    if not message.content.startswith("."):
        command = message.content.split()
        if "bot:" not in message.author.name:
            if message.channel.name not in ["info", "client-information"]:
                channel_name = message.channel.name.split("-")
                server_id = channel_name[1]
                wbh_url = functions.get_webhook_url(
                    message.author.id, server_id)

                if command[0] == "!start":
                    functions.send_webhook(wbh_url, "`Starting server...`")

                    server = serverHandler.ServerHandler(SID=server_id, UID=message.author.id)
                    server.start()
                elif command[0] == "!ip":
                    send_webhook(wbh_url,
                        f"The IP of {message.channel.name.split('-')[0]} is `0.0.0.0:{message.channel.name.split('-')[1]}0`"
                    )

            elif command[0] == "!terminate":
                if get(message.author.roles, name="Admin"):
                    SID = command[1]
                    reason = " ".join(command[2:])
                    print(f"[Termination] Recieved termination of {SID} for reason '{reason}'.")
                    UID = open(f"./servers/{SID}/owner.txt", "r").read()
                    server_name = json.load(open(f"./userdata/{UID}.json", "r"))["server"]["name"]
                    user = await bot.fetch_user(int(UID))
                    await user.send("# Notice of Termination\n"
                                    f"We would like to inform you that your server that goes by the name of `{server_name}` has unfortunately been terminated. This is a final decision that has been discussed over by the moderation team and cannot be undone. We do this to assure that all servers are being kept within our server rules.\n"
                                    f"## Reason for termination:\n"
                                    f" `{reason}`\n"
                                    f"Actioned by: `{message.author.name}`")
                    functions.delete_server(SID)
                    channel = discord.utils.find(
                        lambda c: str(SID).lower() in c.name.lower(),
                        message.guild.channels
                    )
                    if channel:
                        await channel.delete()
                        await message.delete()
                    print(f"[Termination] Server '{SID}' terminated successfully.")




@bot.tree.command(name="create", description="Create a server")
@app_commands.describe(
    name="The name of your server",
    minecraft_version="The version of minecraft for your server",
    software="The software used for your server",
    server_description="Describe your server!")
async def create(inter: discord.Interaction, name: str,
                 server_description: str,
                 minecraft_version: Literal["1.21", "1.20", "1.19", "1.18",
                                            "1.17", "1.16", "1.15", "1.14",
                                            "1.13", "1.12", "1.11", "1.10",
                                            "1.9", "1.8"],
                 software: Literal["Paper", "Spigot"]):
    UID = str(inter.user.id)
    await inter.response.defer(ephemeral=True)
    user_data_path = f"./userdata/{UID}.json"

    if os.path.exists(user_data_path):
        with open(user_data_path, "r") as f:
            f_json = json.load(f)
    else:
        with open(user_data_path, "x") as f:
            f.write(default_json)
            f.close()
            f = open(user_data_path, "r")
            f_json = json.load(f)

    char_err = 0
    wrd_err = 0

    for char in name:
        if char not in string.ascii_letters + string.digits:
            char_err += 1
        else:
            pass
    if char_err > 0:
        await inter.followup.send(
            f"Error! Name cannot contain characters that are not letters or integers",
            ephemeral=True)
        return False

    if len(name) > 10:
        await inter.followup.send(
            "Error! Server name must be under 10 characters long!",
            ephemeral=True)
        return False

    def contains_banned_words(text):
        for word in banned_words:
            if word.upper() in text.upper():
                return True
        return False

    if contains_banned_words(name) or contains_banned_words(
            server_description):
        await inter.followup.send(
            "Error! Name or description cannot contain inappropriate words!",
            ephemeral=True)
        return False


    else:

        try:
            result = await asyncio.to_thread(
                functions.create_server,
                    UID,
                     name,
                    server_description,
                    minecraft_version,
                       software
            )
            server_SID = functions.get_SID(UID=UID)
            if server_SID:
                guild = inter.guild
                user = inter.user
                overwrites = {
                    guild.default_role:
                    discord.PermissionOverwrite(read_messages=False),
                    user:
                    discord.PermissionOverwrite(read_messages=True)
                }
                server_channel = await guild.create_text_channel(
                    name=f"{name}-{server_SID}",
                    overwrites=overwrites
                )
                await server_channel.edit(topic=server_description)
                webhook = await server_channel.create_webhook(
                    name=f"{name} bot:{server_SID}")
                await inter.followup.send("Server created successfully!", ephemeral=True)
                functions.set_webhook_url(UID, webhook.url)
                functions.plugin_config(UID, webhook.url)
                functions.send_webhook(
                    webhook.url, f"Server {name} created successfully")
                functions.send_webhook(
                    webhook.url,
                    f"{inter.user.mention} here's what to do!\n!start - start the server\n!ip - view the ip of your server\n/invite <user> - add a user to the server\n/remove <user> <server_name> - remove a user from a server\n/delete <server_name> - delete a server\n\nIf you want to send a message without executing a command, but a '.' before the message and the server wont read it.\n**Run /help for a list of commands**"
                )
                functions.send_webhook(
                    webhook.url,
                    "**IT IS RECOMENDED THAT YOU MUTE THIS CHANNEL!**")
            else:
                await inter.followup.send(
                    "Failed to create server: You already have 3 servers!",
                    ephemeral=True)
        except Exception as e:
            await inter.followup.send(f"Failed to create server: {e}",
                                     ephemeral=True)
            print(e)


@bot.tree.command(name="delete", description="Delete a server")
@app_commands.describe(server_name="The name of the server to delete")
async def delete(inter: discord.Interaction, server_name: str):
    UID = inter.user.id
    guild = inter.guild
    await inter.response.send_message(f"Deleting {server_name}.",
                                      ephemeral=True)
    SID = functions.get_SID(str(UID))
    print(f"[Server Deletion] [{SID}] Attempting to delete {server_name}`.")
    delete = functions.delete_server(SID)
    if delete:
        channel_name = f"{server_name}-{SID}"
        channel = discord.utils.get(guild.channels, name=channel_name)
        print(f"[Server Deletion] [{SID}] Deleting channel {server_name}-{SID}.")

        if channel:
            await channel.delete()
        else:
            await inter.followup.send(f"[Server Deletion] [{SID}] Error! That server does not exist!",
                                      ephemeral=True)
    else:
        await inter.followup.send(f"[Server Deletion] [{SID}] Error! Unable to delete {server_name}")



@bot.tree.command(name="invite", description="Invite a user to your server")
@app_commands.describe(user="The user you would like to invite")
async def invite(inter: discord.Interaction, user: discord.Member):
    UID = inter.user.id
    guild = inter.guild
    SID = functions.get_SID(UID)
    user_data_path = f"./userdata/{UID}.json"
    print(f"[Server Invite] [{SID}] Invite request for {user} to {SID}.")

    print(f"[Server Invite] [{SID}] Obtaining userdata")
    if not os.path.exists(user_data_path):
        await inter.response.send_message(
            f"No user data found for {UID}.", ephemeral=True)
        return

    with open(user_data_path, "r") as f:
        data = json.load(f)

    print(f"[Server Invite] [{SID}] Checking owner.")
    with open(f"./servers/{SID}/owner.txt", "r") as f:
        owner = f.read()

    if str(UID) == owner:
        print(f"[Server Invite] [{SID}] Adding user.")
        name = f"{data['server']['name']}-{SID}"
        channel = discord.utils.get(guild.channels, name=name)
        print(f"[Server Invite] [{SID}] Rewriting channel permissions.")
        if channel:
            overwrites = channel.overwrites
            overwrites[user] = discord.PermissionOverwrite(read_messages=True)
            await channel.edit(overwrites=overwrites)
            await channel.send(f"{user.mention} has joined!")
            data['server']['users'].append(user.id)
            json.dump(data, open(user_data_path, "w"), indent=4)
        else:
            await inter.response.send_message("Channel not found",
                                              ephemeral=True)
    else:
        await inter.response.send_message(
            "You cannot do this as you are not the owner!", ephemeral=True)



@bot.tree.command(name="leave", description="leave a server")
@app_commands.describe(server_id="The ID of the server you want to leave (name-ID)")
async def leave(inter: discord.Interaction, server_id: str):
    guild = inter.guild
    user = inter.user
    UID = inter.user.id


    owner_file_path = f"./servers/{server_id}/owner.txt"


    if os.path.exists(owner_file_path):
        with open(owner_file_path, "r") as f:
            owner = f.read()
    else:
        await inter.response.send_message("That server does not exist!",
                                              ephemeral=True)
        return
    with open(f"./userdata/{owner}.json") as f:
        name = json.load(f)['server']['name']

    channel = discord.utils.get(guild.channels, name=f"{name}-{server_id}")

    if user.name == owner:
        await inter.response.send_message(
            "You cannot leave as you are the owner!", ephemeral=True)
    else:
        owner_data_path = f"./userdata/{owner}.json"
        with open(owner_data_path, "r") as f:
            data = json.load(f)
            data["server"]["users"].remove(user.id)
        with open(owner_data_path, "w") as fw:
            json.dump(data, fw, indent=4)
        overwrites = channel.overwrites
        overwrites[user] = discord.PermissionOverwrite(
            read_messages=False)
        await channel.edit(overwrites=overwrites)
        await inter.response.send_message(f"{user.name} has left!")


@bot.tree.command(name="kick", description="Kick a user from your server")
@app_commands.describe(user="The user you want to kick from the server")
async def kick(inter: discord.Interaction, user: discord.Member):
    guild = inter.guild
    UID = inter.user.id
    SID = functions.get_SID(UID)
    owner_file_path = f"./servers/{SID}/owner.txt"

    if os.path.exists(owner_file_path):
        with open(owner_file_path, "r") as f:
            owner = f.read().strip()
    else:
        await inter.response.send_message("Owner file does not exist!",
                                          ephemeral=True)
        return

    if str(UID) != owner:
        await inter.response.send_message(
            "You cannot kick as you are not the owner!", ephemeral=True)
        return
    elif str(user.id) == owner:
        await inter.response.send_message("You cannot kick yourself!",
                                          ephemeral=True)
        return
    else:
        with open(f"./userdata/{UID}.json", "r") as f:
            data = json.load(f)
            data["server"]["users"].remove(user.id)
        with open(f"./userdata/{UID}.json", "w") as fw:
            json.dump(data, fw, indent=4)
        channel = discord.utils.get(guild.channels, name=f"{data['server']['name']}-{SID}")
        overwrites = channel.overwrites
        overwrites[user] = discord.PermissionOverwrite(read_messages=False)
        await channel.edit(overwrites=overwrites)
        await inter.response.send_message(f"{user.mention} kicked successfully!")


@bot.tree.command(name="help", description="Get help on Hosty commands")
@app_commands.describe(command="The command you need help with")
async def help_command(inter: discord.Interaction,
                       command: Optional[Literal["create", "delete", "list",
                                                 "invite", "leave", "kick",
                                                 "help", "resetpassword",
                                                 "info"]] = None):
    if command is None:
        await inter.response.send_message(
            f"# {inter.user.mention} list of commands:\n"
            "`/create <name> <description> <version> <software> <password>` - Create a server\n"
            "`/delete` - delete your server\n"
            "`/list` - list your servers\n"
            "`/invite <user>` - invite a player to your server\n"
            "`/leave` - leave a server\n"
            "`/kick <user>` - kick a player from your server\n"
            "`/info` - display info about the specified server\n"
            "## Use /help <command> for more info on a command",
            ephemeral=True)
    elif command == "create":
        await inter.response.send_message(
            f"# {inter.user.mention} **/help**\n"
            "The create command creates you a personal server. With the argument 'name', you can set the name of your server to your choice. Description will set the server's description, version will set the server's version, and Software will set the server type. This command will create you a private channel that gives you access to the server's console.\n"
            "## Recommendations for making a server\n"
            "If you are making a survival multiplayer server for you and your friends, Paper focuses on performance so you will be not very likely to lag. If you are making a server where you are going to do something bigger and with more players, Spigot is good for that as it starts the server very quickly and will adjust to the number of players on the server currently. Just to note that you can only have 1 server per person.",
            ephemeral=True)
    elif command == "delete":
        await inter.response.send_message(
            f"# {inter.user.mention} **/help**\n"
            "The delete command will delete a server that **you own**. It will not delete servers that are not yours. This command will delete the server files and you will not be able to get it back after deleting it.",
            ephemeral=True)
    elif command == "invite":
        await inter.response.send_message(
            f"# {inter.user.mention} **/help**\n"
            "The invite command will invite a player of your choice to your server. The argument 'user' is required and will specify the user that you are inviting to the server. This command will give the user access to the server channel and lets the player read the console and run server commands. If you have made a mistake and you did not want to invite the user, you can run /kick <user> and it will kick the specified user from the server.",
            ephemeral=True)
    elif command == "leave":
        await inter.response.send_message(
            f"# {inter.user.mention} **/help**\n"
            "The leave command will let you leave a server. This will stop you from being able to access the server's console. The argument 'server_id' is required to specify what server you are leaving. The ID can be found in the side of the channel name 'name-ID'",
            ephemeral=True)
    elif command == "kick":
        await inter.response.send_message(
            f"# {inter.user.mention} **/help**\n"
            "The kick command will kick a user from the console. The argument 'user' will specify the user that you are requesting to kick. You can only run this command if you are the creator of the server.",
            ephemeral=True)
    elif command == "info":
        await inter.response.send_message(
            f"# {inter.user.mention} **/help**\n"
            "The info command will display information on your server, this will specify the server that you want to display formation about. It will display the server's name, description, version, software, server ID, owner and users.",
            ephemeral=True)



@bot.tree.command(name="info", description="show info on a server")
async def info(inter: discord.Interaction):
    UID = inter.user.id
    users = None
    try:
        with open(f"./userdata/{UID}.json", "r") as f:
            data = json.load(f)
            SID = functions.get_SID(UID)
            if data["server"]["SID"] == SID:
                for user in data["server"]["users"]:
                    users = f"{users}\n{await bot.fetch_user(user)}"
                await inter.response.send_message(
                    f"Info for: {data['server']['name']}"
                    f"```\nDescription: {data['server']['description']}\n"
                    f"Version: {data['server']['version']}\n"
                    f"Software: {data['server']['software']}\n"
                    f"SID: {data['server']['SID']}\n"
                    f"Owner: {await bot.fetch_user(data['server']['owner'])}```\n"
                    f"Users: ```{users}```",
                    ephemeral=True)
            return
    except Exception as e:
        print(e)


@bot.tree.command(name="clear", description="clear messages in a channel")
@app_commands.describe(
    amount=
    "Number of messages to clear. Defaults to clearing the entire chat if not specified."
)
async def clear(inter: discord.Interaction, amount: int = None):
    try:
        if not get(inter.user.roles, name="Admin"):
            if inter.channel.name not in ["info", "client-information"]:
                if amount is None:
                    await inter.channel.purge()
                    await inter.response.send_message("Chat cleared.",
                                                      ephemeral=True)
                else:
                    deleted = await inter.channel.purge(limit=amount)
                    await inter.response.send_message(
                        f"Deleted {len(deleted)} messages.", ephemeral=True)
            else:
                await inter.response.send_message(f"You cannot do this here!",
                                                  ephemeral=True)
        else:
            if amount is None:
                await inter.channel.purge()
                await inter.response.send_message("Chat cleared.",
                                                  ephemeral=True)
            else:
                deleted = await inter.channel.purge(limit=amount)
                await inter.response.send_message(
                    f"Deleted {len(deleted)} messages.", ephemeral=True)
    except Exception:
        pass


@bot.tree.command(name="property", description="Change a property of a server")
@app_commands.describe(
                       property="The name of the property",
                       new_definition="The new definition of the property")
async def property(inter: discord.Interaction,
                   property: Literal["motd", "player limit", "gamemode", "pvp",
                                     "difficulty", "online_mode",
                                     "allow_flight", "allow_nether", "require_resource_pack", "list"],
                   new_definition: str = None):
    UID = inter.user.id
    SID = functions.get_SID(UID)
    file_path = f"./servers/{str(SID)}/server.properties"

    if new_definition is None and property != "list":
        await inter.response.send_message(
            "Oops! You need to enter a new definition for this one.",
            ephemeral=True
        )
        return False

    with open(file_path, "r") as f:
        contents = f.readlines()

    with open(file_path, "w") as fw:
        for line in contents:
            if property == "motd" and line.startswith("motd="):
                line = functions.translate_chat_code(
                    "&", f"motd={new_definition}\n")
            elif property == "player limit" and line.startswith(
                    "max-players="):
                if int(new_definition) > 20:
                    await inter.response.send_message(
                        "Oops! The player limit is set to `20`!",
                        ephemeral=True)
                    return False
                line = f"max-players={new_definition}\n"
            elif property == "gamemode" and line.startswith("gamemode="):
                if new_definition not in [
                        "survival", "creative", "adventure", "spectator"
                ]:
                    await inter.response.send_message(
                        "Oops! That is not a gamemode!", ephemeral=True)
                    return False
                line = f"gamemode={new_definition}\n"
            elif property == "pvp" and line.startswith("pvp="):
                if new_definition not in ["True", "False", "true", "false"]:
                    await inter.response.send_message(
                        "Oops! new defenition must be true or false!",
                        ephemeral=True)
                    return False
                line = f"pvp={new_definition}\n"
            elif property == "difficulty" and line.startswith("difficulty="):
                if new_definition not in [
                        "peaceful", "easy", "normal", "hard"
                ]:
                    await inter.response.send_message(
                        "Oops! Difficulty must be peaceful, easy, normal or hard!",
                        ephemeral=True)
                    return False
                line = f"difficulty={new_definition}\n"
            elif property == "online_mode" and line.startswith("online-mode="):
                if new_definition not in ["True", "False", "true", "false"]:
                    await inter.response.send_message(
                        "Oops! new defenition must be true or false!",
                        ephemeral=True)
                    return False
                line = f"online-mode={new_definition}\n"
            elif property == "allow_flight" and line.startswith(
                    "allow-flight="):
                if new_definition not in ["True", "False", "true", "false"]:
                    await inter.response.send_message(
                        "Oops! new defenition must be true or false!",
                        ephemeral=True)
                    return False
                line = f"allow-flight={new_definition}\n"
            elif property == "allow_nether" and line.startswith(
                    "allow-nether="):
                if new_definition not in ["True", "False", "true", "false"]:
                    await inter.response.send_message(
                        "Oops! new defenition must be true or false!",
                        ephemeral=True)
                    return False
                line = f"allow-nether={new_definition}\n"
            elif property == "require_resource_pack" and line.startswith("require_resource_pack="):
                if new_definition not in ["True", "False", "true", "false"]:
                    await inter.response.send_message(
                        "Oops! new defenition must be true of false!",
                        ephemeral=True)
                    return False
                line = f"require_resource_pack={new_definition}"
            elif property == "list":
                await inter.response.send_message(
                    "## Server Properties\n```" +
                    "\n".join(contents) +
                    "```",
                    ephemeral=True
                )
            fw.write(line + "\n")
    if property != "list":
        await inter.response.send_message(
            f"Changed `{property}` to\n```{new_definition}```",
            ephemeral=True)
    fw.close()
    f.close()

if __name__ == "__main__":
    bot.run(TOKEN)
