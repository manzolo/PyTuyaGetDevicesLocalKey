import tinytuya
from flask import Flask, jsonify, request
#from flask_cors import cross_origin
from api import get_access_token, get_device_info, connect_to_redis
import os
import json
import time

app = Flask(__name__)

# Carica la configurazione
def load_config():
    config_file = "config.secret.json" if os.path.exists("config.secret.json") else "config.json"
    with open(config_file, "r") as jsonfile:
        return json.load(jsonfile)

# API per ottenere i dati da Redis
@app.route("/api/get_devices", methods=["GET"])
#@cross_origin()
def get_devices():
    redis_client = connect_to_redis()
    if not redis_client:
        return jsonify({"error": "Redis non disponibile"}), 500

    devices = {}
    for key in redis_client.keys("*"):
        data = redis_client.hgetall(key)
        devices[key.decode()] = {k.decode(): v.decode() for k, v in data.items()}

    return jsonify(devices)

# API per aggiornare i dispositivi Tuya
@app.route("/api/update_devices", methods=["POST"])
#@cross_origin()
def update_devices():
    try:
        redis_client = connect_to_redis()
        if not redis_client:
            return jsonify({"error": "Redis non disponibile"}), 500

        tuyatime = str(int(time.time()) * 1000)

        # Chiamata a get_device_info con gestione degli errori
        try:
            access_token = get_access_token(ClientID, ClientSecret, BaseUrl, EmptyBodyEncoded, tuyatime, DEBUG)
            get_device_info(ClientID, ClientSecret, BaseUrl, EmptyBodyEncoded, tuyatime, access_token, deviceList, redis_client, DEBUG)
        except Exception as e:
            print(f"Errore durante l'aggiornamento dei dispositivi: {e}")
            return jsonify({"error": str(e)}), 500

        return jsonify({"message": "Update complete"}), 200

    except Exception as e:
        print(f"Errore generico in update_devices: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/check_device_status", methods=["POST"])
def check_device_status():
    data = request.json
    device_id = data.get("device_id")
    local_key = data.get("local_key")
    private_ip = data.get("private_ip")

    try:
        device = tinytuya.OutletDevice(device_id, private_ip, local_key)
        device.set_version("3.3")  # Imposta la versione del protocollo
        # Imposta un timeout di 1 secondo
        device.set_socketTimeout(1.0)
        status = device.status()

        print(status)
        return jsonify({"status": "online" if status.get("dps") else "offline"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/toggle_device", methods=["POST"])
def toggle_device():
    data = request.json
    device_id = data.get("device_id")
    local_key = data.get("local_key")
    private_ip = data.get("private_ip")
    command = True if data.get("command") == "on" else False # "on" o "off"

    try:
        # Invia il comando
        device = tinytuya.OutletDevice(device_id, private_ip, local_key)
        device.set_version("3.3")
        payload = device.generate_payload(tinytuya.CONTROL, {"1": command})
        response = device._send_receive(payload)

        if response:
            return jsonify({"message": f"Device turned {command}"}), 200
        else:
            return jsonify({"error": str(response)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

configData = load_config()
ClientID = configData["ClientID"]
ClientSecret = configData["ClientSecret"]
BaseUrl = configData["BaseUrl"]
deviceList = configData["deviceList"]
EmptyBodyEncoded = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
DEBUG = configData.get("Debug", "false").lower() in ("true", "1", "t", "yes")

if __name__ == "__main__":
    if DEBUG:
        # Modalità sviluppo: usa il server integrato di Flask
        app.run(host="0.0.0.0", port=80, debug=True)
    else:
        # Modalità produzione: usa un server WSGI (gunicorn)
        from gunicorn.app.base import BaseApplication

        class FlaskApplication(BaseApplication):
            def __init__(self, app, options=None):
                self.application = app
                self.options = options or {}
                super().__init__()

            def load_config(self):
                for key, value in self.options.items():
                    self.cfg.set(key, value)

            def load(self):
                return self.application

        options = {
            "bind": "0.0.0.0:80",
            "workers": 4,  # Numero di worker (puoi regolarlo in base alle tue esigenze)
            "timeout": 120,  # Timeout per le richieste
        }
        FlaskApplication(app, options).run()