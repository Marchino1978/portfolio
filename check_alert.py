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
            "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=10a11bd1-4e03-4d43-90b6-50eb8acf4ba6&token=6a0b8cab-6042-4131-a13c-3aa0353a3576&response=html",
            "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=a4e68b99-76fb-43a1-b9b9-6428412fb64f&token=3e015bc8-9a10-4007-bd67-f77bdf39c426&response=html",
            "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=9f3fe9e8-246c-454b-a327-84b29a2be979&token=ff7788c2-3aeb-4466-ac58-b848c1ebced4&response=html",
            "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=46fdcd85-a9bd-41ba-9496-e354cccd21d3&token=6c59acd4-a3cc-414f-b34b-1ff991cef44a&response=html",
            "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=3b5d291e-ba34-402d-aa9f-f515af9bf753&token=6dd14228-6683-4f79-9f3e-7babe533b01e&response=html",
            "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=e80933c5-1ba6-43ef-a6b0-76de38ea2843&token=d1935f71-d39a-4ca5-9546-75a211c997ec&response=html",
            "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=24ca9054-8114-40de-b2cc-7e8e8dcc719f&token=96ac76f1-7a1f-4629-9240-c76be1c8a17b&response=html"
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