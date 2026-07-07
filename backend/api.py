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

# TTL di default (secondi) oltre il quale un dato di discovery e' considerato stale
DEFAULT_DISCOVERY_TTL = 900


def _decode_hash(raw):
    out = {}
    for k, v in raw.items():
        k = k.decode("utf-8") if isinstance(k, bytes) else k
        v = v.decode("utf-8") if isinstance(v, bytes) else v
        out[k] = v
    return out


def get_local_discovery(redis_client, device_id):
    """Legge il record di discovery locale ('discovery:<id>') da Redis."""
    if not redis_client:
        return None
    try:
        raw = redis_client.hgetall(f"discovery:{device_id}")
    except Exception:
        return None
    if not raw:
        return None
    return _decode_hash(raw)


def apply_local_network_info(redis_client, device_id, data, discovery_ttl=DEFAULT_DISCOVERY_TTL):
    """
    Sovrascrive private_ip / mac_address di `data` con i valori AUTORITATIVI
    ottenuti dalla discovery locale (Redis 'discovery:<id>'), se ancora freschi.

    Il cloud Tuya non e' affidabile per IP/MAC (li scambia tra device doppioni):
    qui ci si fida solo di discovery UDP (IP) + Pi-hole/ARP (MAC).

    Imposta i flag 'ip_stale' / 'mac_stale' (stringhe "true"/"false") e 'mac_source'.
    `data` deve gia' contenere i valori di fallback (config/cloud), usati se la
    discovery e' assente o troppo vecchia.
    """
    disc = get_local_discovery(redis_client, device_id)
    fresh = False
    if disc and disc.get("last_seen"):
        try:
            fresh = (time.time() - float(disc["last_seen"])) <= discovery_ttl
        except (ValueError, TypeError):
            fresh = False

    if fresh and disc.get("ip"):
        data["private_ip"] = disc["ip"]
        data["ip_stale"] = "false"
        if disc.get("mac"):
            data["mac_address"] = disc["mac"]
            data["mac_stale"] = "false"
            data["mac_source"] = disc.get("mac_source", "")
        else:
            # IP fresco ma MAC non risolto: teniamo il MAC di fallback ma lo segnaliamo
            data["mac_stale"] = "true"
            data["mac_source"] = ""
    else:
        # discovery assente/stale: mostriamo comunque il dato di fallback ma segnalato
        data["ip_stale"] = "true"
        data["mac_stale"] = "true"
        data["mac_source"] = ""
    return data

def get_access_token(ClientID, ClientSecret, BaseUrl, EmptyBodyEncoded, tuyatime, debug=False):
    try:
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

        # Effettua la richiesta GET
        response = requests.get(BaseUrl + URL, headers=headers)
        response.raise_for_status()  # Solleva un'eccezione per codici di stato HTTP non 2xx

        # Parsing della risposta JSON
        AccessTokenResponse = response.json()
        if debug:
            print("AccessTokenResponse is now", AccessTokenResponse)

        # Verifica se la risposta indica un errore
        if not AccessTokenResponse.get("success", False):
            error_code = AccessTokenResponse.get("code")
            error_msg = AccessTokenResponse.get("msg")
            raise ValueError(f"Errore API Tuya: Code {error_code}, Message: {error_msg}")

        # Estrai l'access token dalla risposta
        AccessToken = AccessTokenResponse.get("result", {}).get("access_token")
        if debug:
            print("Access token is now", AccessToken)

        if not AccessToken:
            raise ValueError("Access token non found on response")

        return AccessToken

    except requests.exceptions.HTTPError as http_error:
        # Gestione degli errori HTTP (4xx, 5xx)
        print(f"Errore HTTP durante la richiesta: {http_error}")
        print(f"Risposta del server: {http_error.response.text}")
        raise  # Rilancia l'eccezione per gestirla a livello superiore

    except requests.exceptions.RequestException as req_error:
        # Gestione degli errori di rete o di configurazione della richiesta
        print(f"Errore durante la richiesta: {req_error}")
        raise  # Rilancia l'eccezione per gestirla a livello superiore

    except ValueError as val_error:
        # Gestione degli errori di parsing o dati mancanti
        print(f"Errore nei dati della risposta: {val_error}")
        raise  # Rilancia l'eccezione per gestirla a livello superiore

    except Exception as e:
        # Gestione di altri errori imprevisti
        print(f"Errore imprevisto: {e}")
        raise  # Rilancia l'eccezione per gestirla a livello superiore

def get_device_info(ClientID, ClientSecret, BaseUrl, EmptyBodyEncoded, tuyatime, AccessToken, deviceList, redis_client, debug=False, print_results=False, discovery_ttl=DEFAULT_DISCOVERY_TTL):
    try:
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

            # Effettua la richiesta GET
            response = requests.get(BaseUrl + URL, headers=headers)
            response.raise_for_status()  # Solleva un'eccezione per codici di stato HTTP non 2xx
            RequestResponse = response.json()

            if debug:
                print("RequestResponse is now", RequestResponse)

            # Verifica se la risposta indica un errore
            if not RequestResponse.get("success", False):
                error_code = RequestResponse.get("code")
                error_msg = RequestResponse.get("msg")
                raise ValueError(f"API Tuya error: Code {error_code}, Message: {error_msg}")

            # Estrai le informazioni dei dispositivi
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
                # Valori di FALLBACK statici da config (usati solo se la discovery
                # locale e' assente/stale). NON sono affidabili di per se'.
                private_ip = deviceList.get(id, {}).get("private_ip", "N/A")
                mac_address = deviceList.get(id, {}).get("mac_address", "N/A")
                last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                entry = {
                    "local_key": localKey,
                    "custom_name": customName,
                    "ip": ip,                    # IP dal cloud: inaffidabile, tenuto solo per debug
                    "is_online": is_online,
                    "model": model,
                    "name": name,
                    "product_id": product_id,
                    "private_ip": private_ip,    # fallback config -> sovrascritto da discovery
                    "mac_address": mac_address,  # fallback config -> sovrascritto da Pi-hole/ARP
                    "last_updated": last_updated,
                }
                # NON fidarsi di IP/MAC del cloud: usa la discovery locale autoritativa
                apply_local_network_info(redis_client, id, entry, discovery_ttl)
                # Redis non accetta valori None
                entry = {k: ("" if v is None else v) for k, v in entry.items()}

                if redis_client:
                    try:
                        redis_client.hset(f"{id}", mapping=entry)
                        if debug:
                            print(f"Dispositivo {id} salvato in Redis.")
                    except Exception as redis_error:
                        print(f"Error on Redis save for device {id}: {redis_error}")

                if print_results:
                    print(f"Device {id}:")
                    print(f"  Local Key: {localKey}")
                    print(f"  Custom Name: {customName}")
                    print(f"  IP: {ip}")
                    print(f"  Online: {is_online}")
                    print(f"  Model: {model}")
                    print(f"  Name: {name}")
                    print(f"  Product ID: {product_id}")
                    ip_note = " (stale)" if entry.get("ip_stale") == "true" else ""
                    mac_note = " (stale)" if entry.get("mac_stale") == "true" else \
                        f" [{entry.get('mac_source')}]" if entry.get("mac_source") else ""
                    print(f"  Private IP: {entry['private_ip']}{ip_note}")
                    print(f"  MAC Address: {entry['mac_address']}{mac_note}")
                    print(f"  Last Updated: {last_updated}")
                    print("-" * 40)

    except requests.exceptions.HTTPError as http_error:
        # Gestione degli errori HTTP (4xx, 5xx)
        print(f"HTTP error during request: {http_error}")
        print(f"Error on server response: {http_error.response.text}")
        raise  # Rilancia l'eccezione per gestirla a livello superiore

    except requests.exceptions.RequestException as req_error:
        # Gestione degli errori di rete o di configurazione della richiesta
        print(f"Error during request: {req_error}")
        raise  # Rilancia l'eccezione per gestirla a livello superiore

    except ValueError as val_error:
        # Gestione degli errori dell'API Tuya (es. success: false)
        print(f"Error on response data: {val_error}")
        raise  # Rilancia l'eccezione per gestirla a livello superiore

    except Exception as e:
        # Gestione di altri errori imprevisti
        print(f"Unexpected error on get_device_info: {e}")
        raise  # Rilancia l'eccezione per gestirla a livello superiore

def get_redis_cached_data(redis_client, device_id=None, discovery_ttl=DEFAULT_DISCOVERY_TTL):
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
                decoded = _decode_hash(data)
                apply_local_network_info(redis_client, device_id, decoded, discovery_ttl)
                return {device_id: decoded}
            else:
                return {}
        else:
            # Recupera i dati per tutti i dispositivi (escluse le chiavi di discovery)
            devices = {}
            for key in redis_client.keys("*"):
                key_str = key.decode("utf-8") if isinstance(key, bytes) else key
                if key_str.startswith("discovery:"):
                    continue
                decoded = _decode_hash(redis_client.hgetall(key))
                apply_local_network_info(redis_client, key_str, decoded, discovery_ttl)
                devices[key_str] = decoded
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
    discovery_ttl = int(configData.get("DiscoveryTTL", DEFAULT_DISCOVERY_TTL))
    EmptyBodyEncoded = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    tuyatime = str(int(time.time()) * 1000)

    if debug:
        print("Tuyatime is now", tuyatime)

    redis_client = connect_to_redis()

    if use_cache:
        # Recupera i dati da Redis
        cached_data = get_redis_cached_data(redis_client, discovery_ttl=discovery_ttl)
        if print_results:
            for device_id, data in cached_data.items():
                print(f"Device {device_id}:")
                for key, value in data.items():
                    print(f"  {key}: {value}")
                print("-" * 40)
    else:
        # Recupera i dati dall'API
        access_token = get_access_token(ClientID, ClientSecret, BaseUrl, EmptyBodyEncoded, tuyatime, debug)
        get_device_info(ClientID, ClientSecret, BaseUrl, EmptyBodyEncoded, tuyatime, access_token, deviceList, redis_client, debug, print_results, discovery_ttl)

if __name__ == "__main__":
    # Configura gli argomenti da riga di comando
    parser = argparse.ArgumentParser(description="Recupera i dati dei dispositivi Tuya.")
    parser.add_argument("--cache", action="store_true", help="Usa i dati memorizzati in Redis invece di chiamare l'API.")
    parser.add_argument("--print", action="store_true", help="Stampa i risultati a video.")
    args = parser.parse_args()

    # Se eseguito da CLI, stampa i risultati a video
    main(print_results=args.print, use_cache=args.cache)