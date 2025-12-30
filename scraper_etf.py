import os
import json
import base64
import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
from supabase_client import supabase, upsert_previous_close
from config import is_market_open
from utils.logger import log_info, log_error

# ---------------------------------------------------------
# CARICAMENTO LISTA ETF
# ---------------------------------------------------------
with open("etfs.json", "r") as f:
    ETFS = json.load(f)

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ---------------------------------------------------------
# CONFIGURAZIONE VARIAZIONI (FILE ESTERNO)
# ---------------------------------------------------------

# Mappa dei periodi:
# D = 1 DAY
# W = 1 WEEK
# M = 1 MONTH (30 giorni)
# Q = 3 MONTHS (90 giorni)
# H = 6 MONTHS (180 giorni)
# Y = 1 YEAR (365 giorni)
# 3 = 3 YEARS
# 5 = 5 YEARS
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


def load_variation_config():
    """
    Legge il file config/variations.conf e restituisce un dict:
    {
      "v1": "D",
      "v2": "W",
      "v3": "M",
      "v_led": "M"
    }
    """
    config = {}
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "config", "variations.conf")

        if not os.path.exists(path):
            log_error(f"File di configurazione variazioni non trovato: {path}")
            return config

        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    # Rimuove eventuali commenti inline dopo il valore
                    if "#" in value:
                        value = value.split("#", 1)[0].strip()
                    config[key] = value

        log_info(f"Configurazione variazioni caricata: {config}")
    except Exception as e:
        log_error(f"Errore lettura variations.conf: {e}")

    return config


# ---------------------------------------------------------
# FUNZIONI PER VARIAZIONI MULTI-PERIODO
# ---------------------------------------------------------
def get_price_on_or_before(symbol, target_date):
    """
    Recupera il prezzo di close più vicino a target_date andando indietro.
    Usa la tabella previous_close su Supabase.
    """
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

        log_info(f"[WARN] Nessun prezzo storico trovato per {symbol} fino a {target_str}")
        return None
    except Exception as e:
        log_error(f"Errore get_price_on_or_before({symbol}, {target_date}): {e}")
        return None


def calc_variation(price_today, price_past):
    """
    Calcola la variazione percentuale tra price_today e price_past.
    """
    if price_today is None or price_past is None:
        return None
    try:
        return ((price_today - price_past) / price_past) * 100.0
    except ZeroDivisionError:
        return None


def fmt_variation(value, suffix):
    """
    Formatta la variazione come stringa:
    +0.13%D, -0.22%W, N/A, ecc.
    """
    if value is None:
        return "N/A"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}%{suffix}"


def compute_all_variations(symbol, price_today, today_date):
    """
    Calcola tutte le variazioni multi-periodo per un singolo ETF.
    Restituisce un dict con chiavi = codice periodo (D, W, M, Q, H, Y, 3, 5)
    e valori = stringhe formattate (+0.13%D, N/A, ecc.).
    """
    results = {}

    for code, (days, suffix) in PERIODS.items():
        target_date = today_date - timedelta(days=days)
        past_price = get_price_on_or_before(symbol, target_date)
        variation = calc_variation(price_today, past_price)
        results[code] = fmt_variation(variation, suffix)

    return results


# ---------------------------------------------------------
# SALVATAGGIO market.json STATICO (FORMATO ESP32)
# ---------------------------------------------------------
def save_market_json(results, market_open):
    try:
        os.makedirs("data", exist_ok=True)
        path = os.path.join("data", "market.json")

        data_array = []

        for symbol, etf in results.items():
            if etf.get("status") == "unavailable":
                continue

            # dailyChange rimane per compatibilità con ESP32 attuale
            daily_change_str = (
                f"{etf['daily_change']:.2f}"
                if etf.get("daily_change") is not None
                else "-"
            )

            entry = {
                "symbol": etf["symbol"],
                "label": etf["label"],
                "price": etf["price"],
                "dailyChange": daily_change_str,
                "value": etf["price"],
            }

            # Se abbiamo già calcolato v1, v2, v3, v_led li aggiungiamo
            # (non rompiamo nulla se non ci sono)
            if "v1" in etf:
                entry["v1"] = etf["v1"]
            if "v2" in etf:
                entry["v2"] = etf["v2"]
            if "v3" in etf:
                entry["v3"] = etf["v3"]
            if "v_led" in etf:
                entry["v_led"] = etf["v_led"]

            data_array.append(entry)

        json_output = {
            "status": "APERTO" if market_open else "CHIUSO",
            "values": {
                "data": data_array
            }
        }

        with open(path, "w") as f:
            json.dump(json_output, f, indent=2)

        log_info(f"market.json aggiornato in {path}")

    except Exception as e:
        log_error(f"Errore salvataggio market.json: {e}")


# ---------------------------------------------------------
# COMMIT AUTOMATICO SU GITHUB (API)
# ---------------------------------------------------------
def commit_to_github():
    try:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            log_error("GITHUB_TOKEN non impostato nelle variabili d'ambiente")
            return

        repo = "Marchino1978/portfolio"
        path = "data/market.json"
        api_url = f"https://api.github.com/repos/{repo}/contents/{path}"

        # 1. Leggi il file locale
        with open(path, "rb") as f:
            content = f.read()

        encoded = base64.b64encode(content).decode("utf-8")

        # 2. Recupera SHA del file esistente (se c’è)
        sha = None
        get_resp = requests.get(api_url, headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        })

        if get_resp.status_code == 200:
            sha = get_resp.json().get("sha")

        # 3. Prepara payload
        payload = {
            "message": "Update market.json",
            "content": encoded,
            "branch": "main"
        }

        if sha:
            payload["sha"] = sha

        # 4. PUT → commit automatico
        put_resp = requests.put(api_url, headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        }, json=payload)

        if put_resp.status_code in (200, 201):
            log_info("Commit su GitHub completato via API")
        else:
            log_error(f"Errore GitHub API: {put_resp.status_code} - {put_resp.text}")

    except Exception as e:
        log_error(f"Errore commit GitHub API: {e}")


# ---------------------------------------------------------
# SCRAPING PREZZO
# ---------------------------------------------------------
def scrape_price(item_id):
    url = f"https://www.ls-tc.de/de/etf/{item_id}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        mid = soup.find("span", attrs={"field": "mid", "item": f"{item_id}@1"})
        if mid:
            return float(mid.text.strip().replace(",", "."))
    except Exception as e:
        log_error(f"Errore scraping {item_id}: {e}")
    return None


# ---------------------------------------------------------
# LETTURA PREVIOUS CLOSE (giorno precedente)
# ---------------------------------------------------------
def get_previous_close(symbol):
    today = date.today().isoformat()

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

    log_info(f"[WARN] Nessun previous_close trovato per {symbol} prima di {today}")
    return None


# ---------------------------------------------------------
# AGGIORNAMENTO COMPLETO ETF
# ---------------------------------------------------------
def update_all_etf():
    today_date = date.today()
    today_str = today_date.isoformat()
    market_open = is_market_open()

    # Carichiamo la configurazione delle variazioni (v1, v2, v3, v_led)
    variation_config = load_variation_config()

    results = {}

    for etf in ETFS:
        symbol = etf["symbol"]
        label = etf["label"]

        price = scrape_price(etf["item_id"])
        if price is None:
            results[symbol] = {"status": "unavailable"}
            continue

        prev = get_previous_close(symbol)

        daily_change = None
        if prev is not None:
            try:
                daily_change = round(((price - prev) / prev) * 100, 2)
            except ZeroDivisionError:
                daily_change = None

        if market_open:
            upsert_previous_close(
                symbol=symbol,
                label=label,
                close_value=price,
                snapshot_date=today_str,
                daily_change=daily_change
            )

        # Calcolo di tutte le variazioni multi-periodo
        all_variations = compute_all_variations(symbol, price, today_date)
        # all_variations è un dict tipo:
        # { "D": "+0.13%D", "W": "-0.22%W", "M": "+1.10%M", ... }

        # Mapping secondo il file di configurazione
        # Se manca qualcosa in config, fallback a D/W/M/M
        v1_code = variation_config.get("v1", "D")
        v2_code = variation_config.get("v2", "W")
        v3_code = variation_config.get("v3", "M")
        v_led_code = variation_config.get("v_led", "M")

        v1_value = all_variations.get(v1_code, "N/A")
        v2_value = all_variations.get(v2_code, "N/A")
        v3_value = all_variations.get(v3_code, "N/A")
        v_led_value = all_variations.get(v_led_code, "N/A")

        results[symbol] = {
            "symbol": symbol,
            "label": label,
            "price": price,
            "previous_close": prev,
            "daily_change": daily_change,
            "snapshot_date": today_str,
            "status": "open" if market_open else "closed",
            # nuovi campi per ESP32 (multi-variazione)
            "v1": v1_value,
            "v2": v2_value,
            "v3": v3_value,
            "v_led": v_led_value,
        }

    log_info(f"Aggiornamento ETF completato: {len(results)} simboli")

    save_market_json(results, market_open)
    commit_to_github()

    return results, market_open
