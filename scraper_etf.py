import os
import json
import base64
import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo

import bot_telegram
from supabase_client import get_supabase, upsert_previous_close
from config import is_market_open
from utils.logger import log_info, log_error

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# ---------------------------------------------------------
# PERIODI MULTI-VARIAZIONE
# ---------------------------------------------------------
PERIODS = {
    "D":  (1,      "D"),
    "W":  (7,      "W"),
    "M":  (30,     "M"),
    "Q":  (90,     "Q"),
    "H":  (180,    "H"),
    "Y":  (365,    "Y"),
    "3":  (365*3,  "3Y"),
    "5":  (365*5,  "5Y"),
}

# ---------------------------------------------------------
# CARICAMENTO ETF
# ---------------------------------------------------------
def load_etfs():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "etfs.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            etfs = json.load(f)
        log_info(f"Caricati {len(etfs)} ETF da etfs.json")
        return etfs
    except Exception as e:
        log_error(f"Errore lettura etfs.json: {e}")
        return []

# ---------------------------------------------------------
# CONFIGURAZIONE VARIAZIONI
# ---------------------------------------------------------
def load_variation_config():
    config = {}
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "config", "variations.conf")

        if not os.path.exists(path):
            log_error(f"File variazioni non trovato: {path}")
            return {"v1": "D", "v2": "W", "v3": "M", "v_led": "M", "v_alert": "M", "v_bot": "M"}  # fallback sicuri

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.split("#", 1)[0].strip()
                    config[key] = value

        log_info(f"Configurazione variazioni caricata: {config}")
    except Exception as e:
        log_error(f"Errore lettura variations.conf: {e}")

    return config

# ---------------------------------------------------------
# SCRAPING PREZZO
# ---------------------------------------------------------
def scrape_price(item_id):
    url = f"https://www.ls-tc.de/de/etf/{item_id}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        mid = soup.find("span", attrs={"field": "mid", "item": f"{item_id}@1"})
        if mid and mid.text.strip():
            return float(mid.text.strip().replace(",", "."))
        log_error(f"Prezzo non trovato per item_id {item_id}")
    except Exception as e:
        log_error(f"Errore scraping {item_id}: {e}")
    return None

# ---------------------------------------------------------
# PREVIOUS CLOSE & VARIAZIONI
# ---------------------------------------------------------
def get_previous_close(symbol, supabase):
    today = date.today().isoformat()
    try:
        resp = (
            supabase.table("previous_close")
            .select("close_value")
            .eq("symbol", symbol)
            .filter("snapshot_date", "lt", today)
            .order("snapshot_date", desc=True)
            .limit(1)
            .execute()
        )
        if resp.data:
            return resp.data[0]["close_value"]
    except Exception as e:
        log_error(f"Errore query previous_close {symbol}: {e}")
    return None

def get_price_on_or_before(symbol, target_date, supabase):
    try:
        target_str = target_date.isoformat()
        resp = (
            supabase.table("previous_close")
            .select("close_value")
            .eq("symbol", symbol)
            .filter("snapshot_date", "lte", target_str)
            .order("snapshot_date", desc=True)
            .limit(1)
            .execute()
        )
        if resp.data:
            return float(resp.data[0]["close_value"])
    except Exception as e:
        log_error(f"Errore get_price_on_or_before({symbol}, {target_date}): {e}")
    return None

def calc_variation(price_today, price_past):
    if price_today is None or price_past is None or price_past == 0:
        return None
    return ((price_today - price_past) / price_past) * 100.0

def fmt_variation(value, suffix):
    if value is None:
        return "N/A"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}%{suffix}"

def compute_all_variations(symbol, price_today, today_date, supabase):
    results = {}
    for code, (days, suffix) in PERIODS.items():
        target_date = today_date - timedelta(days=days)
        past_price = get_price_on_or_before(symbol, target_date, supabase)
        variation = calc_variation(price_today, past_price)
        results[code] = fmt_variation(variation, suffix)
    return results

# ---------------------------------------------------------
# SALVATAGGIO market.json
# ---------------------------------------------------------
def save_market_json(results, market_open):
    try:
        os.makedirs("data", exist_ok=True)
        path = os.path.join("data", "market.json")

        now = datetime.now(ZoneInfo("Europe/Rome"))
        readable = now.strftime("%H:%M %d-%m-%Y")

        data_array = []
        for symbol, etf in results.items():
            if etf.get("status") == "unavailable":
                continue

            daily_change_str = (
                f"{etf['daily_change']:+.2f}" if etf.get("daily_change") is not None else "-"
            )

            entry = {
                "symbol": etf["symbol"],
                "label": etf["label"],
                "price": round(etf["price"], 4),
                "dailyChange": daily_change_str,
                "value": round(etf["price"], 4),
            }

            for key in ("v1", "v2", "v3", "v_led", "v_alert", "v_bot"):
                if key in etf:
                    entry[key] = etf[key]

            data_array.append(entry)

        json_output = {
            "status": "APERTO" if market_open else "CHIUSO",
            "open": market_open,
            "values": {"source": "ls-tc.de", "data": data_array},
            "last_updated": {
                "iso": now.isoformat(),
                "readable": readable
            }
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(json_output, f, indent=2, ensure_ascii=False)

        log_info(f"market.json salvato con {len(data_array)} ETF")

    except Exception as e:
        log_error(f"Errore salvataggio market.json: {e}")

# ---------------------------------------------------------
# COMMIT GITHUB
# ---------------------------------------------------------
def commit_to_github():
    path = "data/market.json"
    try:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            log_error("GITHUB_TOKEN non impostato – commit GitHub saltato")
            return

        repo = "Marchino1978/portfolio"
        api_url = f"https://api.github.com/repos/{repo}/contents/{path}"

        with open(path, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf-8")

        sha = None
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        }
        get_resp = requests.get(api_url, headers=headers, timeout=10)
        if get_resp.status_code == 200:
            sha = get_resp.json().get("sha")

        payload = {
            "message": "Update market.json [auto]",
            "content": content,
            "branch": "main"
        }
        if sha:
            payload["sha"] = sha

        put_resp = requests.put(api_url, headers=headers, json=payload, timeout=10)
        if put_resp.status_code in (200, 201):
            log_info("Commit market.json su GitHub completato")
        else:
            log_error(f"Errore commit GitHub: {put_resp.status_code} – {put_resp.text}")

    except Exception as e:
        log_error(f"Errore durante commit GitHub: {e}")

# ---------------------------------------------------------
# FUNZIONE PRINCIPALE
# ---------------------------------------------------------
def update_all_etf():
    log_info("=== INIZIO aggiornamento ETF ===")
    today_date = date.today()
    today_str = today_date.isoformat()
    market_open = is_market_open()

    supabase = get_supabase()
    ETFS = load_etfs()
    if not ETFS:
        log_error("Nessun ETF caricato – aggiornamento interrotto")
        return {}, market_open

    variation_config = load_variation_config()

    results = {}

    for etf in ETFS:
        symbol = etf["symbol"]
        label = etf["label"]
        item_id = etf["item_id"]

        log_info(f"Scraping {symbol} ({label}) – item_id {item_id}")
        price = scrape_price(item_id)

        if price is None:
            results[symbol] = {"status": "unavailable", "symbol": symbol, "label": label}
            continue

        prev = get_previous_close(symbol, supabase)
        daily_change = calc_variation(price, prev) if prev else None

        if market_open:
            upsert_previous_close(
                symbol=symbol,
                label=label,
                close_value=price,
                snapshot_date=today_str,
                daily_change=daily_change
            )

        all_variations = compute_all_variations(symbol, price, today_date, supabase)

        results[symbol] = {
            "symbol": symbol,
            "label": label,
            "price": price,
            "previous_close": prev,
            "daily_change": daily_change,
            "snapshot_date": today_str,
            "status": "open" if market_open else "closed",
            "v1": all_variations.get(variation_config.get("v1", "D"), "N/A"),
            "v2": all_variations.get(variation_config.get("v2", "W"), "N/A"),
            "v3": all_variations.get(variation_config.get("v3", "M"), "N/A"),
            "v_led": all_variations.get(variation_config.get("v_led", "M"), "N/A"),
            "v_alert": all_variations.get(variation_config.get("v_alert", "M"), "N/A"),
            "v_bot": all_variations.get(variation_config.get("v_bot", "M"), "N/A"),
        }

    save_market_json(results, market_open)
    commit_to_github()

    # ---------------------------------------------------------
    # REPORT TELEGRAM (Logica per weekend e giorni feriali)
    # ---------------------------------------------------------
    now_rome = datetime.now(ZoneInfo("Europe/Rome"))
    giorno_settimana = now_rome.weekday() # 0=Lunedì, 6=Domenica

    # Definiamo se dobbiamo inviare il report oggi
    invia_oggi = False

    # CASO 1: Oggi è il 1° del mese ed è un giorno lavorativo (Lun-Ven)
    if now_rome.day == 1 and giorno_settimana < 5:
        invia_oggi = True

    # CASO 2: Il 1° era Sabato o Domenica e oggi è Lunedì (2 o 3 del mese)
    elif giorno_settimana == 0 and (now_rome.day == 2 or now_rome.day == 3):
        invia_oggi = True

    # Esegui l'invio solo nella finestra oraria del primo cron (07:10 - 07:20)
    if invia_oggi and 10 <= now_rome.minute <= 20 and now_rome.hour == 7:
        log_info(f"Condizione report soddisfatta ({now_rome.day}/{now_rome.month}). Invio...")
        try:
            import bot_telegram
            bot_telegram.send_monthly_report()
            log_info("Report Telegram inviato con successo.")
        except Exception as e:
            log_error(f"Errore invio Telegram: {e}")

    log_info(f"=== FINE aggiornamento ETF – {len([r for r in results.values() if r.get('status') != 'unavailable'])} ETF aggiornati ===")
    return results, market_open