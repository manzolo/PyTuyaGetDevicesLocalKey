import json
import redis
import os
import logging

# Configura il logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connessione a Redis
def connect_to_redis():
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    try:
        redis_client = redis.Redis(host=redis_host, port=redis_port, db=0)
        redis_client.ping()  # Verifica la connettività
        logger.info("Connesso a Redis con successo.")
        return redis_client
    except redis.ConnectionError as e:
        logger.error(f"Errore di connessione a Redis: {e}")
        return None

# Estrai tutti i dati da Redis
def dump_redis_data(redis_client, output_file="redis_dump.json"):
    if not redis_client:
        logger.error("Redis non è disponibile.")
        return

    try:
        # Ottieni tutte le chiavi
        keys = redis_client.keys("*")
        data = {}

        # Estrai i valori per ogni chiave
        for key in keys:
            key_type = redis_client.type(key).decode("utf-8")
            if key_type == "string":
                value = redis_client.get(key).decode("utf-8")
            elif key_type == "hash":
                value = redis_client.hgetall(key)
                value = {k.decode("utf-8"): v.decode("utf-8") for k, v in value.items()}
            elif key_type == "list":
                value = redis_client.lrange(key, 0, -1)
                value = [v.decode("utf-8") for v in value]
            elif key_type == "set":
                value = redis_client.smembers(key)
                value = [v.decode("utf-8") for v in value]
            elif key_type == "zset":
                value = redis_client.zrange(key, 0, -1, withscores=True)
                value = {v[0].decode("utf-8"): v[1] for v in value}
            else:
                value = "Tipo non supportato"

            data[key.decode("utf-8")] = value

        # Salva i dati in un file JSON
        with open(output_file, "w") as f:
            json.dump(data, f, indent=4)

        #logger.info(f"Dati di Redis salvati in {output_file}")

        # Stampa il contenuto del file su stdout
        with open(output_file, "r") as f:
            print(f.read())

    except Exception as e:
        logger.error(f"Errore durante l'estrazione dei dati: {e}")

# Main
if __name__ == "__main__":
    redis_client = connect_to_redis()
    if redis_client:
        dump_redis_data(redis_client)