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
            "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=2cafe29b-c908-4765-a6cf-4a5e9f15617f&token=2ba96808-f8eb-468e-a89d-9fb8664a2957&response=html",
            "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=e40c4980-5012-4460-8977-a2ff38975e1b&token=9896269f-464c-473b-9b2f-c8102ce8b94e&response=html",
            "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=e8e31137-e363-42dd-a8c0-a70f5d9eecb5&token=5b5f22b6-e212-4694-9326-095f7ba54df1&response=html",
            "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=dee08f89-b4f8-4005-98a0-3f78c40007ef&token=0c0debf8-8c81-48ae-8de8-f9605871b24d&response=html",
            "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=090dd6ee-8672-4434-afb0-c1d9da9d97cc&token=9cf5d5b1-2246-4657-b7a4-2e3f43a4bbe8&response=html",
            "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=93decff5-e613-443f-9007-d689f91800a7&token=9c3a1e7d-a8ed-4f12-a240-757578645e56&response=html",
            "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=469d7076-46c1-444f-b09a-ca02a578ed99&token=c54c36b6-13b1-458d-85d2-764157d2cb09&response=html"
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