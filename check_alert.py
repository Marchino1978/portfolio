import os
import json
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from utils.logger import log_info, log_error

def get_config():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    conf_path = os.path.join(base_dir, "config", "variations.conf")
    conf = {}
    with open(conf_path, "r") as f:
        for line in f:
            if "=" in line:
                name, value = line.split("=", 1)
                conf[name.strip()] = value.split("#")[0].strip()
    return conf

def check_alert():
    try:
        now = datetime.now(ZoneInfo("Europe/Rome"))
        if now.weekday() > 4: return "weekend"
        if not (now.hour == 19 and 10 <= now.minute <= 20): return "wrong_time"

        conf = get_config()
        
        urls = [
            "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=ca398444-ff26-4158-a877-4081007ef4ab&token=02cbbd5e-7717-4cdb-9b68-6522bf9920ea&response=html",
            "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=ee507dd2-aa02-4021-91cc-4e92f7fc9edd&token=1e5a73b6-732d-4636-a9d6-9e6c565a7639&response=html",
            "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=cdf03dcc-c35d-4e31-bc37-c11d0ed389ec&token=8d450f96-5535-4432-8daa-dcef305c60d4&response=html",
            "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=f4f7ae99-0eac-4aae-97cf-a5f0841fb0c1&token=e1effc48-e25d-4ec7-987a-3bb8dcd536e4&response=html",
            "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=32094a58-cdaa-4484-9bfe-4c031b11c9e8&token=1e7e9bd3-e05b-4e2f-a8b6-93ce33e968e9&response=html",
            "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=1cddc615-9d94-4ef8-bd52-f252caeb72bb&token=306d120e-a999-4e28-aa94-9673073f155a&response=html",
            "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=301554c6-6677-4cfb-b29a-b404c60e414f&token=753488a9-1b9a-42d8-af20-e8bb63642df8&response=html"
        ]

        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "market.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        etfs = data.get("values", {}).get("data", [])
        best_idx = -1

        for etf in etfs:
            v = etf.get(conf["v_alert"], "N/A")
            if v == "N/A": continue
            
            val_str = v.replace("%", "").replace("+", "").strip()
            if val_str and val_str[-1].isalpha(): val_str = val_str[:-1]
            val = float(val_str)

            if val <= float(conf["s_alert_6"]):   idx = 6
            elif val <= float(conf["s_alert_5"]): idx = 5
            elif val <= float(conf["s_alert_4"]): idx = 4
            elif val <= float(conf["s_alert_3"]): idx = 3
            elif val <= float(conf["s_alert_2"]): idx = 2
            elif val <= float(conf["s_alert_1"]): idx = 1
            elif val <= float(conf["s_alert_0"]): idx = 0
            else: idx = -1

            if idx > best_idx: best_idx = idx

        if best_idx != -1:
            requests.get(urls[best_idx], timeout=10)
            log_info(f"ALERTER: Attivato Switch_{best_idx}")
            return "triggered"

        return "no_alert"

    except Exception as e:
        log_error(f"Errore: {e}")
        return "error"