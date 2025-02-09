import os
import hashlib
import hmac

import redis
import requests
import time
import json
import logging

from typing import Dict, List

def get_access_token(ClientID, ClientSecret, BaseUrl, EmptyBodyEncoded, tuyatime, debug = False):
    # Get Access Token
    URL = "/v1.0/token?grant_type=1"

    StringToSign = f"{ClientID}{tuyatime}GET\n{EmptyBodyEncoded}\n\n{URL}"
    if debug:
        print("StringToSign is now", StringToSign)

    AccessTokenSign = hmac.new(ClientSecret.encode(), StringToSign.encode(), hashlib.sha256).hexdigest().upper()
    if debug:
        print("AccessTokenSign is now", AccessTokenSign)

    headers = {
        "sign_method": "HMAC-SHA256",
        "client_id": ClientID,
        "t": tuyatime,
        "mode": "cors",
        "Content-Type": "application/json",
        "sign": AccessTokenSign
    }

    AccessTokenResponse = requests.get(BaseUrl + URL, headers=headers).json()
    if debug:
        print("AccessTokenResponse is now", AccessTokenResponse)

    AccessToken = AccessTokenResponse.get("result", {}).get("access_token")
    if debug:
        print("Access token is now", AccessToken)

    return AccessToken

def get_device_info(ClientID, ClientSecret, BaseUrl, EmptyBodyEncoded, tuyatime, AccessToken, deviceList, redis_available,debug = False):
    device_ids = list(deviceList.keys())  # Converti le chiavi in una lista

    # Suddividi la lista di ID in blocchi da 20 dispositivi
    chunk_size = 20
    chunks = split_into_chunks(device_ids, chunk_size)  # Passa la lista, non il dizionario

    for chunk in chunks:
        # Crea una stringa con gli ID dei dispositivi nel blocco corrente
        device_ids = ",".join(chunk)

        # Send Device status request
        URL = f"/v2.0/cloud/thing/batch?device_ids={device_ids}"

        StringToSign = f"{ClientID}{AccessToken}{tuyatime}GET\n{EmptyBodyEncoded}\n\n{URL}"
        if debug:
            print("StringToSign is now", StringToSign)

        RequestSign = hmac.new(ClientSecret.encode(), StringToSign.encode(), hashlib.sha256).hexdigest().upper()
        if debug:
            print("RequestSign is now", RequestSign)

        headers = {
            "sign_method": "HMAC-SHA256",
            "client_id": ClientID,
            "t": tuyatime,
            "mode": "cors",
            "Content-Type": "application/json",
            "sign": RequestSign,
            "access_token": AccessToken
        }

        RequestResponse = requests.get(BaseUrl + URL, headers=headers).json()
        if debug:
            print("RequestResponse is now", RequestResponse)

        devices_info = RequestResponse.get("result", [])
        for device_info in devices_info:
            id = device_info.get("id")
            localKey = device_info.get("local_key")
            customName = device_info.get("custom_name")
            ip = device_info.get("ip")
            is_online = str(device_info.get("is_online"))
            model = device_info.get("model")
            name = device_info.get("name")
            product_id= device_info.get("product_id")
            print(f"{id}\t{localKey}\t{customName}")

            # Salva le informazioni del dispositivo in Redis solo se Redis è disponibile
            if redis_available:
                redis_client.hset(f"{id}", mapping={
                    "local_key": localKey,
                    "custom_name": customName,
                    "ip": ip,
                    "is_online": is_online,
                    "model": model,
                    "name": name,
                    "product_id": product_id
                })
                if debug:
                    print(f"Dispositivo {id} salvato in Redis.")

# Funzione per suddividere una lista in blocchi di dimensione specificata
def split_into_chunks(lst: List, chunk_size: int) -> List[List]:
    """Divide una lista in blocchi di dimensione specificata."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

# Set debug value to True or False to (de)activate output
debug = True

# Configura il logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Connessione a Redis
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", 6379))
redis_available = True

try:
    redis_client = redis.Redis(host=redis_host, port=redis_port, db=0)
    redis_client.ping()  # Verifica la connettività
except redis.ConnectionError:
    redis_available = False
    logger.warning("Redis non è disponibile. I dati non verranno salvati in Redis.")

# Verifica se esiste il file config.secret.json, altrimenti usa config.json
config_file = "config.secret.json" if os.path.exists("config.secret.json") else "config.json"

# Leggi il file di configurazione
with open(config_file, "r") as jsonfile:
    configData = json.load(jsonfile)
    if debug:
        print("Read successful")


# Declare constants
ClientID = configData["ClientID"]
ClientSecret = configData["ClientSecret"]
BaseUrl = configData["BaseUrl"]
deviceList = configData["deviceList"]
EmptyBodyEncoded = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
tuyatime = str(int(time.time()) * 1000)

if debug:
    print("Tuyatime is now", tuyatime)

# Ottenere il token di accesso
access_token = get_access_token(ClientID, ClientSecret, BaseUrl, EmptyBodyEncoded,tuyatime, debug)

#La seguente response significa che un id non è stato trovato, forse è stato sostituito perchè guasto?
#{
#  "code": 40001900,
#  "msg": "No space permission",
#  "success": false,
#  ...
#}

# Ottenere informazioni sui dispositivi
get_device_info(ClientID, ClientSecret, BaseUrl, EmptyBodyEncoded, tuyatime, access_token, deviceList, redis_available, debug)
