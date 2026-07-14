import json
import os
import random
from logging import exception
import shutil
import requests
import URLs
import subprocess




def generate_server(v, s, SID, u):    
    print(f"[Server Generation] Recieved version: {v}, Software: {s}, SID: {SID}")
    print(f"[Server Generation] [{SID}] Mapping URLS")
    url_mapping = {
        "Spigot": {
            "1.21": URLs.S_1_21,
            "1.20": URLs.S_1_20,
            "1.19": URLs.S_1_19,
            "1.18": URLs.S_1_18,
            "1.17": URLs.S_1_17,
            "1.16": URLs.S_1_16,
            "1.15": URLs.S_1_15,
            "1.14": URLs.S_1_14,
            "1.13": URLs.S_1_13,
            "1.12": URLs.S_1_12,
            "1.11": URLs.S_1_11,
            "1.10": URLs.S_1_10,
            "1.9": URLs.S_1_9,
            "1.8": URLs.S_1_8
        },
        "Paper": {
            "1.21": URLs.P_1_21,
            "1.20": URLs.P_1_20,
            "1.19": URLs.P_1_19,
            "1.18": URLs.P_1_18,
            "1.17": URLs.P_1_17,
            "1.16": URLs.P_1_16,
            "1.15": URLs.P_1_15,
            "1.14": URLs.P_1_14,
            "1.13": URLs.P_1_13,
            "1.12": URLs.P_1_12,
            "1.11": URLs.P_1_11,
            "1.10": URLs.P_1_10,
            "1.9": URLs.P_1_9,
            "1.8": URLs.P_1_8
        }
    }

    if s in url_mapping and v in url_mapping[s]:
        url = url_mapping[s][v]
        try:
            print(f"[Server Generation] [{SID}] Downloading server jar")
            print(f"[Server Generation] [{SID}] Downloading from {url}")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            with open(f"./servers/{str(SID)}/server.jar", "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        f.flush()
        except Exception as e:
            print(f"[Server Generation] [{SID}] Error downloading server jar: {e}")
    else:
        raise ValueError("Invalid server type or version")

    print(f"[Server Generation] [{SID}] Writing run script")
    run_f = open(f"./servers/{str(SID)}/run.sh", "w")
    run_f.write("java -Xmx200m -Xms200m -jar server.jar --nogui")
    run_f.close()

    run_f = open(f"./servers/{str(SID)}/run.bat", "w")
    run_f.write("java -Xmx200m -Xms200m -jar server.jar --nogui")
    run_f.close()

    print(f"[Server Generation] [{SID}] Writing eula")
    eula = open(f"./servers/{str(SID)}/eula.txt", "w")
    eula.write("eula=true")
    eula.close()

    print(f"[Server Generation] [{SID}] Defining server owner")
    owner = open(f"./servers/{str(SID)}/owner.txt", "w")
    owner.write(u)
    owner.close()

    print(f"[Server Generation] [{SID}] Writing server properties")
    properties = open(f"./servers/{str(SID)}/server.properties", "w")
    properties_default_file = open(f"./server_properties.txt")
    properties_default = properties_default_file.read()
    properties_default = properties_default.replace("[SID]", str(SID))
    properties.write(properties_default)
    properties_default_file.close()
    properties.close()
    
    print(f"[Server Generation] [{SID}] Updating permissions")
    #subprocess.run(["chmod", "+x", f"./servers/{str(SID)}/run.sh"])
    # subprocess.run(["./run.sh"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def gen_SID():
    SID = ""
    for i in range(4):
        SID += str(random.randint(0, 5))
    with open("./SIDs.txt", "r") as f:
        existing_SIDs = [line.split('-')[0] for line in f.read().splitlines()]
    if SID.startswith("0"):
        return gen_SID()
    if SID in existing_SIDs:
        return gen_SID()
    else:
        return SID

def create_server(UID: str, name: str, description: str, version: str, software: str):
    file_path = f"./userdata/{UID}.json"
    print("[Server Creation] Generating ID")
    server_SID = gen_SID()
    print(f"[Server Creation] [{server_SID}] ID generated: {server_SID}")
    server_base_path = f"./servers/{server_SID}/"

    print(f"[Server Creation] [{server_SID}] Creating server Directory")
    if not os.path.exists(server_base_path):
        os.makedirs(server_base_path)
        generate_server(s=software, v=version, SID=server_SID, u=UID)

    print(f"[Server Creation] [{server_SID}] Checking user avaliability")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            data = json.load(f)
    else:
        data = {"server":{}}

    print(f"[Server Creation] [{server_SID}] Updating Userdata")
    data["server"] = {
        "name": name,
        "description": description,
        "version": version,
        "software": software,
        "path": server_base_path,
        "SID": server_SID,
        "owner": UID,
        "webhook_url": None,
        "users": []
    }

    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

    print(f"[Server Creation] [{server_SID}] Dumping server ID")
    with open("./SIDs.txt", "a") as sid_file:
        sid_file.write(f"{server_SID}-{UID}\n")

    os.system("ls")
    return True

def delete_server(SID: str) -> bool:
    print(f"[Server Deletion] [{SID}] Locating owner.")
    owner = open(f"./servers/{SID}/owner.txt", "r").read()
    owner_userdata = f"./userdata/{owner}.json"

    print(f"[Server Deletion] [{SID}] Locating owner userdata.")
    if os.path.exists(owner_userdata):
            print(f"[Server Deletion] [{SID}] Locating server.")
            server_path = f"./servers/{SID}"
            if os.path.exists(server_path):
                print(f"[Server Deletion] [{SID}] Deleting server.")
                shutil.rmtree(server_path)
            print(f"[Server Deletion] [{SID}] Resetting userdata")
            os.remove(owner_userdata)
            print(f"[Server Deletion] [{SID}] Removing server ID.")
            sids_file_path = "./SIDs.txt"
            with open(sids_file_path, "r") as sids_file:
                SIDs = [line.strip() for line in sids_file]

            with open(sids_file_path, "w") as sids_file:
                for line in SIDs:
                    if line.split("-")[0] != SID:
                          sids_file.write(line + "\n")

            print(f"[Server Deletion] [{SID}] Server deleted successfully.")
            return True
    else:
        return False

def get_SID(UID: str):
    path = f"./userdata/{UID}.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
            if data["server"] != {}:
                return data["server"]["SID"]
    else:
        return False



def send_webhook(URL=None, content=None):
    data = {
        "content": content
    }
    response = requests.post(URL, data=json.dumps(data), headers={"Content-Type": "application/json"})

    if response.status_code == 204:
        return True
    else:
        return False

def set_webhook_url(UID, url):
    file_path = f"./userdata/{UID}.json"

    with open(file_path, "r") as f:
        data = json.load(f)
        if data["server"] != {}:
            data["server"]["webhook_url"] = url
            with open(file_path, "w") as fw:
                json.dump(data, fw, indent=4)
        else:
            return False

def get_webhook_url(UID, SID):
    with open(f"./userdata/{UID}.json", "r") as f:
        data = json.load(f)
        if data["server"] != {}:
            url = data["server"].get("webhook_url")
            return url
        else:
            return False

def plugin_config(UID,url):
    SID = get_SID(UID)
    os.chdir(f"./servers/{str(SID)}/")
    os.mkdir("plugins")
    os.mkdir("./plugins/Hosty/")
    os.chdir("./plugins/Hosty")
    plugin_config = open("./config.yml", "w")
    config = f"""
    # Hosty configurations

    # The webhook URL that is used in the channel
    url: '{url}'

    # The port that is used to communicate with discord
    port: {SID}1
    """
    plugin_config.write(config)
    plugin_config.close()
    os.chdir("../../../../")

def translate_chat_code(char, string):
    color_codes = {
        '0': '\\u00A70',  # Black
        '1': '\\u00A71',  # Dark Blue
        '2': '\\u00A72',  # Dark Green
        '3': '\\u00A73',  # Dark Aqua
        '4': '\\u00A74',  # Dark Red
        '5': '\\u00A75',  # Dark Purple
        '6': '\\u00A76',  # Gold
        '7': '\\u00A77',  # Gray
        '8': '\\u00A78',  # Dark Gray
        '9': '\\u00A79',  # Blue
        'a': '\\u00A7a',  # Green
        'b': '\\u00A7b',  # Aqua
        'c': '\\u00A7c',  # Red
        'd': '\\u00A7d',  # Light Purple
        'e': '\\u00A7e',  # Yellow
        'f': '\\u00A7f',  # White
        'k': '\\u00A7k',  # Obfuscated
        'l': '\\u00A7l',  # Bold
        'm': '\\u00A7m',  # Strikethrough
        'n': '\\u00A7n',  # Underline
        'o': '\\u00A7o',  # Italic
        'r': '\\u00A7r',  # Reset
    }

    for code, replacement in color_codes.items():
        string = string.replace(char + code, replacement)

    return string

def get_name(UID: str):
    with open(f"./userdata/{UID}.json", "r") as f:
        data = json.load(f)
        return data["server"]["name"]
