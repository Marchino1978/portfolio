import os
import json
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from utils.logger import log_info, log_error

VSH_URL = "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=2cafe29b-c908-4765-a6cf-4a5e9f15617f&token=2ba96808-f8eb-468e-a89d-9fb8664a2957&response=html"
SOGLIA = 1.0

def check_alert():
    try:
        now = datetime.now(ZoneInfo("Europe/Rome"))
        
        if now.weekday() > 4: return "weekend"
        
        # Logghiamo il minuto esatto per debug
        log_info(f"Controllo alert avviato alle {now.hour}:{now.minute}")

        if not (now.hour == 21 and 10 <= now.minute <= 20):
            return "wrong_time"

        # Percorso assoluto per non sbagliare mai cartella
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "data", "market.json")

        if not os.path.exists(path):
            log_error(f"File non trovato in: {path}")
            return "no_file"

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        etfs = data.get("values", {}).get("data", [])
        
        for etf in etfs:
            v = etf.get("v_alert", "N/A")
            if v == "N/A": continue

            val = float(v.replace("%", "").replace("+", "").strip())
            
            if val > SOGLIA:
                log_info(f"SOGLIA SUPERATA: {etf['symbol']} ({val}%) -> Invio ad Alexa...")
                r = requests.get(VSH_URL, timeout=10)
                log_info(f"Risposta Alexa: {r.status_code}")
                return "triggered"

    except Exception as e:
        log_error(f"Errore in check_alert: {e}")
        return "error"