import os
import hashlib
import hmac
import redis
import requests
import time
import json
import logging
from datetime import datetime
import argparse  # Aggiungi questa importazione

# Configura il logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def get_access_token(ClientID, ClientSecret, BaseUrl, EmptyBodyEncoded, tuyatime, debug=False):
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

def get_device_info(ClientID, ClientSecret, BaseUrl, EmptyBodyEncoded, tuyatime, AccessToken, deviceList, redis_client, debug=False, print_results=False):
    device_ids = list(deviceList.keys())
    chunk_size = 20
    chunks = [device_ids[i:i + chunk_size] for i in range(0, len(device_ids), chunk_size)]

    for chunk in chunks:
        device_ids_str = ",".join(chunk)
        URL = f"/v2.0/cloud/thing/batch?device_ids={device_ids_str}"
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
            product_id = device_info.get("product_id")
            private_ip = deviceList.get(id, {}).get("private_ip", "N/A")
            mac_address = deviceList.get(id, {}).get("mac_address", "N/A")
            last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if redis_client:
                redis_client.hset(f"{id}", mapping={
                    "local_key": localKey,
                    "custom_name": customName,
                    "ip": ip,
                    "is_online": is_online,
                    "model": model,
                    "name": name,
                    "product_id": product_id,
                    "private_ip": private_ip,
                    "mac_address": mac_address,
                    "last_updated": last_updated
                })
                if debug:
                    print(f"Dispositivo {id} salvato in Redis.")

            if print_results:
                print(f"Device {id}:")
                print(f"  Local Key: {localKey}")
                print(f"  Custom Name: {customName}")
                print(f"  IP: {ip}")
                print(f"  Online: {is_online}")
                print(f"  Model: {model}")
                print(f"  Name: {name}")
                print(f"  Product ID: {product_id}")
                print(f"  Private IP: {private_ip}")
                print(f"  MAC Address: {mac_address}")
                print(f"  Last Updated: {last_updated}")
                print("-" * 40)

def get_redis_cached_data(redis_client, device_id=None):
    """
    Recupera i dati memorizzati in Redis per uno o tutti i dispositivi.

    Args:
        redis_client: Il client Redis connesso.
        device_id (str, optional): L'ID del dispositivo specifico. Se None, restituisce tutti i dispositivi.

    Returns:
        dict: Un dizionario contenente i dati memorizzati in Redis.
              Se device_id è specificato, restituisce i dati per quel dispositivo.
              Se device_id è None, restituisce i dati per tutti i dispositivi.
    """
    if not redis_client:
        logger.warning("Redis non è disponibile.")
        return {}

    try:
        if device_id:
            # Recupera i dati per un dispositivo specifico
            data = redis_client.hgetall(device_id)
            if data:
                return {device_id: {k.decode("utf-8"): v.decode("utf-8") for k, v in data.items()}}
            else:
                return {}
        else:
            # Recupera i dati per tutti i dispositivi
            devices = {}
            for key in redis_client.keys("*"):
                data = redis_client.hgetall(key)
                devices[key.decode("utf-8")] = {k.decode("utf-8"): v.decode("utf-8") for k, v in data.items()}
            return devices
    except Exception as e:
        logger.error(f"Errore durante il recupero dei dati da Redis: {e}")
        return {}

def connect_to_redis():
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    try:
        client = redis.Redis(host=redis_host, port=redis_port, db=0)
        client.ping()
        return client
    except redis.ConnectionError:
        logger.warning("Redis non è disponibile. I dati non verranno salvati in Redis.")
        return None

def main(print_results=False, use_cache=False):
    config_file = "config.secret.json" if os.path.exists("config.secret.json") else "config.json"
    with open(config_file, "r") as jsonfile:
        configData = json.load(jsonfile)

    debug = configData.get("Debug", "false").lower() in ("true", "1", "t", "yes")
    ClientID = configData["ClientID"]
    ClientSecret = configData["ClientSecret"]
    BaseUrl = configData["BaseUrl"]
    deviceList = configData["deviceList"]
    EmptyBodyEncoded = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    tuyatime = str(int(time.time()) * 1000)

    if debug:
        print("Tuyatime is now", tuyatime)

    redis_client = connect_to_redis()

    if use_cache:
        # Recupera i dati da Redis
        cached_data = get_redis_cached_data(redis_client)
        if print_results:
            for device_id, data in cached_data.items():
                print(f"Device {device_id}:")
                for key, value in data.items():
                    print(f"  {key}: {value}")
                print("-" * 40)
    else:
        # Recupera i dati dall'API
        access_token = get_access_token(ClientID, ClientSecret, BaseUrl, EmptyBodyEncoded, tuyatime, debug)
        get_device_info(ClientID, ClientSecret, BaseUrl, EmptyBodyEncoded, tuyatime, access_token, deviceList, redis_client, debug, print_results)

if __name__ == "__main__":
    # Configura gli argomenti da riga di comando
    parser = argparse.ArgumentParser(description="Recupera i dati dei dispositivi Tuya.")
    parser.add_argument("--cache", action="store_true", help="Usa i dati memorizzati in Redis invece di chiamare l'API.")
    parser.add_argument("--print", action="store_true", help="Stampa i risultati a video.")
    args = parser.parse_args()

    # Se eseguito da CLI, stampa i risultati a video
    main(print_results=args.print, use_cache=args.cache)