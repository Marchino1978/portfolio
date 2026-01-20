import os
import json
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from utils.logger import log_info, log_error

# Configurazione
VSH_URL = "https://www.virtualsmarthome.xyz/url_routine_trigger/activate.php?trigger=2cafe29b-c908-4765-a6cf-4a5e9f15617f&token=2ba96808-f8eb-468e-a89d-9fb8664a2957&response=html"
SOGLIA = 1.0 

def check_alert():
    try:
        now = datetime.now(ZoneInfo("Europe/Rome"))
        
        # 1) Controllo weekend
        if now.weekday() > 4:
            return "weekend"

        # 2) Log per debug e controllo orario (Finestra per il tuo test delle 22)
        log_info(f"Controllo alert avviato alle {now.hour}:{now.minute}")
        
        # Impostato per le 22:10 - 22:25 come hai chiesto
        if not (now.hour == 19 and 10 <= now.minute <= 20):
            return "wrong_time"

        # 3) Percorso assoluto (sistema identico al bot_telegram che funziona)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "data", "market.json")
        
        if not os.path.exists(path):
            log_error(f"Alert Alexa: market.json non trovato in {path}")
            return "no_file"

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        etfs = data.get("values", {}).get("data", [])

        # 4) Controllo variazioni
        triggered = False
        for etf in etfs:
            v = etf.get("v_alert", "N/A")
            if v == "N/A":
                continue

            try:
                # --- PULIZIA STRINGA "CORAZZATA" ---
                # Toglie %, + e spazi
                val_str = v.replace("%", "").replace("+", "").strip()
                
                # Toglie l'ultima lettera (D, W, M...) se presente
                if val_str and val_str[-1].isalpha():
                    val_str = val_str[:-1]
                
                # Conversione sicura in numero
                val = float(val_str)
                
                if val > SOGLIA:
                    log_info(f"ALERTER: {etf['symbol']} supera soglia ({val}%). Attivo Alexa...")
                    requests.get(VSH_URL, timeout=10)
                    triggered = True
                    break # Notifica inviata, usciamo dal ciclo

            except (ValueError, TypeError) as e:
                # Se un ETF fallisce, lo logga ma continua con gli altri!
                log_error(f"Errore conversione per {etf.get('symbol')}: valore '{v}' non valido.")
                continue

        if not triggered:
            return "no_alert"
        
        return "triggered"

    except Exception as e:
        log_error(f"Errore generale in check_alert: {e}")
        return "error"