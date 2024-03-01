import os
import hashlib
import hmac
import requests
import time
import json

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

def get_device_info(ClientID, ClientSecret, BaseUrl, EmptyBodyEncoded, tuyatime, AccessToken, deviceList, debug = False):

    device_ids = ",".join(deviceList.keys())

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

        print(f"{id}\t{localKey}\t{customName}")


# Set debug value to True or False to (de)activate output
debug = True

with open("config.json", "r") as jsonfile:
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

# Ottenere informazioni sui dispositivi
get_device_info(ClientID, ClientSecret, BaseUrl, EmptyBodyEncoded, tuyatime, access_token, deviceList, debug)
