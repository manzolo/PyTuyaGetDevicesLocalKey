# Tuya Device Info Bulk
This project allows you to retrieve and manage information about Tuya devices. It supports two modes of operation:
* Command Line Interface (CLI) Mode: A fast and simple way to retrieve device information directly from the command line.
* Flask + Docker Mode: A more robust and production-ready setup using Flask as a web server and Docker for containerization.

# Frontend screenshot
![immagine](https://github.com/user-attachments/assets/c4000772-1ff3-4395-a37c-c6d9c6c59654)


# Getting Started
Prerequisites
* Python 3.9 or higher
* Redis (optional, for caching device information)
* Docker (optional, for Flask + Docker mode)

## Usage

# Installation (Using Python 3.12)
1. Clone the repository: `git clone https://github.com/manzolo/PyTuyaGetDevicesLocalKey.git`
2. Navigate to the project directory: `cd PyTuyaGetDevicesLocalKey`
3. Install dependencies: `pip install -r requirements.txt`

# Run the Script
```bash
cd backend
python3 api.py [--cache] [--print]

Options:
    --cache: Retrieve data from Redis instead of calling the Tuya API.
    --print: Print the results to the console.
```

# Config.json example

- ClientID : Tuya ClientId
- ClientSecret : Tuya ClientSecret
- deviceList : Tuya device list

~~~
{
  "ClientID": "daslkj2aeqkjajdslk",
  "ClientSecret": "9308aw908eqw90e8q0w98eqw908e0qw9",
  "BaseUrl": "https://openapi.tuyaeu.com",
  "deviceList":{"2f73bb2ed4a2ee6099csmk": "Main lamp",
              "g573bb2ed4a2aa6099csmd": "Secondary switch",
              "we73bb2ed4a2ee6099cuyk": "Night lamp"}
  }
~~~

# Output:
```
Device 2f73bb2ed4a2ee6099csmk:
  local_key: Fm2;'3sv54feYi`R
  custom_name: Main lamp
  ip: 1.2.3.4
  is_online: False
  model: A60
  name: Smart Lighting Tunable White and Color
  product_id: kimfcuo02prkl21t
  private_ip: N/A
  mac_address: N/A
  last_updated: 2025-02-10 21:08:59
----------------------------------------
Device g573bb2ed4a2aa6099csmd:
  local_key: =a3ZelaoW4D/`xH~
  custom_name: Secondary switch
  ip: 1.2.3.5
  is_online: True
  model: 
  name: switch
  product_id: ....
  private_ip: N/A
  mac_address: N/A
  last_updated: 2025-02-10 21:08:59
----------------------------------------
```

# Docker compose

```
docker compose build tuya-localkey-extractor-backend-image
docker compose build tuya-localkey-extractor-frontend-image
docker compose up api frontend

```
## Frontend
Navigate to http://localhost:5000

## API
```bash
curl http://localhost:5005/api/get_devices
```
Update devices informations:
```bash
curl -X POST http://localhost:5005/api/update_devices
```

## cli

```bash
docker compose up cli
```

## cli-cache (from redis)

```bash
docker compose up cli-cache
```

## turn off

```bash
docker compose down
```

## remove all images

```bash
docker compose down --rmi all
```
