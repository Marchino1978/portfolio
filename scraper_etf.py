import json
import requests
from bs4 import BeautifulSoup
from datetime import date
from supabase_client import supabase, upsert_previous_close
from config import is_market_open
from utils.logger import log_info, log_error

with open("etfs.json", "r") as f:
    ETFS = json.load(f)

HEADERS = {"User-Agent": "Mozilla/5.0"}

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

def get_previous_close(symbol):
    today = date.today().isoformat()
    resp = supabase.table("previous_close") \
        .select("close_value") \
        .eq("symbol", symbol) \
        .lt("snapshot_date", today) \
        .order("snapshot_date", desc=True) \
        .limit(1) \
        .execute()
    return resp.data[0]["close_value"] if resp.data else None

def update_all_etf():
    today_str = date.today().isoformat()
    market_open = is_market_open()

    results = {}
    for etf in ETFS:
        symbol = etf["symbol"]
        price = scrape_price(etf["item_id"])
        if price is None:
            results[symbol] = {"status": "unavailable"}
            continue

        prev = get_previous_close(symbol)

        # Soluzione A: calcolare SEMPRE la daily_change se prev esiste
        daily_change = None
        if prev:
            daily_change = round(((price - prev) / prev) * 100, 2)

        # Salvataggio solo se mercato aperto (come da tua logica)
        if market_open:
            upsert_previous_close(
                symbol=symbol,
                label=etf["label"],
                close_value=price,
                snapshot_date=today_str,
                daily_change=daily_change
            )

        results[symbol] = {
            "symbol": symbol,
            "label": etf["label"],
            "price": price,
            "previous_close": prev,
            "daily_change": daily_change,
            "snapshot_date": today_str,
            "status": "open"
        }

    log_info(f"Aggiornamento ETF completato: {len(results)} simboli")
    return results, market_open
