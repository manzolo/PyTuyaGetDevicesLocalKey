# Installation (Using Python 3.9)
1. Clone the repository: `git clone https://github.com/manzolo/PyTuyaGetDevicesLocalKey.git`
2. Navigate to the project directory: `cd PyTuyaGetDevicesLocalKey`
3. Install dependencies: `pip install -r requirements.txt`

## Usage

### Config.json example

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


### Example:

```bash
python app.py
