from datetime import datetime
from zoneinfo import ZoneInfo
import json
import requests
import os
from utils.logger import log_info, log_error

# Configurazione
VSH_URL = "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=2cafe29b-c908-4765-a6cf-4a5e9f15617f&token=2ba96808-f8eb-468e-a89d-9fb8664a2957&response=html"
SOGLIA = 1.0 

def check_alert():
    try:
        # 1) Controllo giorno (lun–ven)
        now = datetime.now(ZoneInfo("Europe/Rome"))
        if now.weekday() > 4:
            return "weekend"

        # 2) Controllo orario (finestra di 10 minuti per sicurezza)
        # Se lo scraper gira alle 19:10, questa condizione è vera fino alle 19:20
        if not (now.hour == 19 and 10 <= now.minute <= 20):
            return "wrong_time"

        # 3) Leggo market.json (percorso relativo alla root del progetto)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "data", "market.json")
        
        if not os.path.exists(path):
            log_error("Alert Alexa: market.json non trovato")
            return "no_file"

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        etfs = data.get("values", {}).get("data", [])

        # 4) Cerco v_alert sopra soglia
        triggered = False
        for etf in etfs:
            v = etf.get("v_alert", "N/A")
            if v == "N/A":
                continue

            # Pulizia e conversione sicura
            try:
                val = float(v.replace("%", "").replace("+", "").strip())
                if val > SOGLIA:
                    log_info(f"Alert Alexa attivato da {etf['symbol']} con variazione {v}")
                    requests.get(VSH_URL, timeout=10)
                    triggered = True
                    break # Esci al primo ETF che supera la soglia
            except ValueError:
                continue

        return "triggered" if triggered else "no_alert"

    except Exception as e:
        log_error(f"Errore critico in check_alert: {e}")
        return "error"