#!/usr/bin/env python3
"""
local_resolve.py — discovery locale AUTORITATIVA di IP e MAC dei dispositivi Tuya.

Perche' esiste:
  Il cloud Tuya restituisce IP/MAC inaffidabili: per i dispositivi identici
  (doppioni) li scambia tra loro. Questo servizio NON si fida del cloud e ricava:
    - IP reale  -> discovery UDP Tuya locale: i device annunciano gwId<->IP da soli
    - MAC reale -> reservation DHCP di Pi-hole (autoritativo IP<->MAC),
                   con fallback sulla tabella ARP dell'host (/proc/net/arp)
  e li scrive in Redis nelle chiavi "discovery:<device_id>" con un timestamp.
  api.py / server.py fondono questi dati SOPRA a quelli del cloud, fidandosi del
  cloud solo per: nome, id, local_key, last_update.

Va eseguito in un container con --network host: serve sia per ricevere i
broadcast UDP Tuya sulla LAN sia per leggere la tabella ARP reale dell'host.
"""
import os
import sys
import time
import json
import socket
import logging

import redis
import tinytuya

logging.basicConfig(level=logging.INFO, format="%(asctime)s [discovery] %(message)s")
log = logging.getLogger("discovery")

CONFIG_FILE = "config.secret.json" if os.path.exists("config.secret.json") else "config.json"

# porta locale usata dai device Tuya (per forzare la risoluzione ARP)
TUYA_PORT = 6668


def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def connect_redis():
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", 6379))
    client = redis.Redis(host=host, port=port, db=0)
    client.ping()
    return client


def _norm_mac(mac):
    if not mac:
        return ""
    return mac.strip().upper().replace("-", ":")


def scan_tuya(scan_intensity):
    """Discovery UDP Tuya -> {device_id: ip}. L'IP arriva dai device stessi."""
    found = {}
    try:
        raw = tinytuya.deviceScan(False, scan_intensity)
    except Exception as exc:  # pragma: no cover
        log.warning(f"deviceScan fallita: {exc}")
        return found
    for ip, info in raw.items():
        device_id = info.get("gwId") or info.get("id")
        device_ip = info.get("ip") or ip
        if device_id:
            found[device_id] = device_ip
    return found


def pihole_ip_to_mac(cfg):
    """IP->MAC dalle reservation DHCP di Pi-hole (autoritativo). Best-effort."""
    ph = cfg.get("Pihole") or {}
    base = (ph.get("BaseUrl") or "").rstrip("/")
    password = ph.get("Password")
    if not base or not password:
        return {}

    import requests
    verify = ph.get("VerifyTls", False)
    if not verify:
        try:
            requests.packages.urllib3.disable_warnings()  # noqa
        except Exception:
            pass

    out = {}
    sid = None
    try:
        resp = requests.post(f"{base}/api/auth", json={"password": password},
                             verify=verify, timeout=8)
        resp.raise_for_status()
        sid = ((resp.json() or {}).get("session") or {}).get("sid")
        if not sid:
            log.warning("Pi-hole: nessun SID ottenuto")
            return {}
        headers = {"X-FTL-SID": sid}
        rr = requests.get(f"{base}/api/config/dhcp/hosts", headers=headers,
                          verify=verify, timeout=8)
        if rr.ok:
            hosts = (((rr.json() or {}).get("config") or {}).get("dhcp") or {}).get("hosts") or []
            for entry in hosts:
                parts = entry.split(",")
                if len(parts) >= 2:
                    mac, ip = parts[0].strip(), parts[1].strip()
                    if ip:
                        out[ip] = _norm_mac(mac)
    except Exception as exc:
        log.warning(f"query Pi-hole fallita: {exc}")
    finally:
        if sid:
            try:
                requests.delete(f"{base}/api/auth", headers={"X-FTL-SID": sid},
                                verify=verify, timeout=5)
            except Exception:
                pass
    return out


def prime_arp(ip):
    """Forza la risoluzione ARP aprendo un socket verso il device (porta Tuya)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.3)
        try:
            s.connect((ip, TUYA_PORT))
        except Exception:
            pass
        finally:
            s.close()
    except Exception:
        pass


def arp_ip_to_mac():
    """IP->MAC dalla tabella ARP dell'host (/proc/net/arp). Fallback."""
    out = {}
    try:
        with open("/proc/net/arp", "r") as f:
            next(f, None)  # salta l'header
            for line in f:
                cols = line.split()
                if len(cols) >= 4:
                    ip, mac = cols[0], cols[3]
                    if mac and mac != "00:00:00:00:00:00":
                        out[ip] = _norm_mac(mac)
    except Exception as exc:
        log.warning(f"lettura ARP fallita: {exc}")
    return out


def resolve_once(rc, cfg):
    scan_intensity = int(cfg.get("DiscoveryScanTimeout", 8))
    devices = scan_tuya(scan_intensity)
    if not devices:
        log.info("nessun device Tuya scoperto in questo giro")
        return 0

    ph_map = pihole_ip_to_mac(cfg)

    # scalda la tabella ARP verso gli IP appena scoperti, poi la rilegge
    for ip in set(devices.values()):
        prime_arp(ip)
    arp_map = arp_ip_to_mac()

    now = str(int(time.time()))
    from_pihole = 0
    from_arp = 0
    for device_id, ip in devices.items():
        mac = ph_map.get(ip, "")
        source = ""
        if mac:
            source = "pihole"
            from_pihole += 1
        else:
            mac = arp_map.get(ip, "")
            if mac:
                source = "arp"
                from_arp += 1
        rc.hset(f"discovery:{device_id}", mapping={
            "ip": ip,
            "mac": mac,
            "mac_source": source,
            "last_seen": now,
        })

    log.info(f"scoperti {len(devices)} device "
             f"(MAC: {from_pihole} da Pi-hole, {from_arp} da ARP, "
             f"{len(devices) - from_pihole - from_arp} non risolti)")
    return len(devices)


def main():
    cfg = load_config()
    interval = int(cfg.get("DiscoveryInterval", 90))
    try:
        rc = connect_redis()
    except Exception as exc:
        log.error(f"Redis non raggiungibile: {exc}")
        sys.exit(1)
    log.info(f"avvio loop discovery (interval={interval}s, config={CONFIG_FILE})")
    while True:
        try:
            resolve_once(rc, cfg)
        except Exception as exc:
            log.warning(f"giro discovery fallito: {exc}")
        time.sleep(interval)


if __name__ == "__main__":
    main()
