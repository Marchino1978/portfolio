import os
import json
import base64
import requests
from bs4 import BeautifulSoup
from datetime import date
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

            entry = {
                "symbol": etf["symbol"],
                "label": etf["label"],
                "price": etf["price"],
                "dailyChange": (
                    f"{etf['daily_change']:.2f}"
                    if etf["daily_change"] is not None
                    else "-"
                ),
                "value": etf["price"]
            }
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
# LETTURA PREVIOUS CLOSE
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
    today_str = date.today().isoformat()
    market_open = is_market_open()

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
            daily_change = round(((price - prev) / prev) * 100, 2)

        if market_open:
            upsert_previous_close(
                symbol=symbol,
                label=label,
                close_value=price,
                snapshot_date=today_str,
                daily_change=daily_change
            )

        results[symbol] = {
            "symbol": symbol,
            "label": label,
            "price": price,
            "previous_close": prev,
            "daily_change": daily_change,
            "snapshot_date": today_str,
            "status": "open" if market_open else "closed"
        }

    log_info(f"Aggiornamento ETF completato: {len(results)} simboli")

    save_market_json(results, market_open)
    commit_to_github()

    return results, market_open
