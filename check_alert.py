import os
import json
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from utils.logger import log_info, log_error

# URL Trigger Alexa (Virtual Smart Home)
VSH_URL = "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=2cafe29b-c908-4765-a6cf-4a5e9f15617f&token=2ba96808-f8eb-468e-a89d-9fb8664a2957&response=html"

def get_alert_config():
    """Legge la soglia dal file config/variations.conf"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    conf_path = os.path.join(base_dir, "config", "variations.conf")
    
    config = {}
    with open(conf_path, "r") as f:
        for line in f:
            if "=" in line:
                name, value = line.split("=", 1)
                config[name.strip()] = value.split("#")[0].strip()
    
    # Restituisce la soglia come numero (es. -20.0)
    return float(config["s_alert"])

def check_alert():
    try:
        now = datetime.now(ZoneInfo("Europe/Rome"))
        if now.weekday() > 4: return "weekend"

        # Finestra di controllo (attualmente ore 22:10 per i tuoi test)
        log_info(f"Controllo alert avviato alle {now.hour}:{now.minute}")
        if not (now.hour == 19 and 10 <= now.minute <= 20):
            return "wrong_time"

        # Carica la soglia dal file conf
        SOGLIA = get_alert_config()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "data", "market.json")
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        etfs = data.get("values", {}).get("data", [])
        triggered = False

        for etf in etfs:
            v = etf.get("v_alert", "N/A")
            if v == "N/A": continue

            try:
                # Pulizia corazzata: toglie %, +, e l'ultima lettera (M, D, W...)
                val_str = v.replace("%", "").replace("+", "").strip()
                if val_str and val_str[-1].isalpha():
                    val_str = val_str[:-1]
                
                val = float(val_str)

                # LOGICA INTELLIGENTE: 
                # Se la soglia è negativa (<0), controlla se il valore è sceso SOTTO (crash)
                # Se la soglia è positiva (>0), controlla se il valore è salito SOPRA (gain)
                if (SOGLIA < 0 and val < SOGLIA) or (SOGLIA > 0 and val > SOGLIA):
                    log_info(f"ALERTER: {etf['symbol']} ({val}%) ha superato la soglia di {SOGLIA}%!")
                    requests.get(VSH_URL, timeout=10)
                    triggered = True
                    break 

            except Exception as e:
                log_error(f"Errore conversione per {etf.get('symbol')}: {e}")
                continue

        return "triggered" if triggered else "no_alert"

    except Exception as e:
        log_error(f"Errore generale check_alert: {e}")
        return "error"