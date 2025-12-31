# ./app.py
----------------------------------------
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, jsonify, send_from_directory
import os
import json

# Import dei moduli (NON delle funzioni)
import scraper_etf
import scraper_fondi

# Import logger per tracciare bene cosa succede
from utils.logger import log_info, log_error

app = Flask(__name__, static_folder="public", static_url_path="")


# ---------------------------------------------------------
# PAGINE STATICHE
# ---------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory("public", "market.html")

@app.route("/market-mobile")
def market_mobile():
    return send_from_directory("public", "market-mobile.html")

@app.route("/salvadanaio")
def salvadanaio():
    return send_from_directory("public", "salvadanaio.html")


# ---------------------------------------------------------
# HEALTHCHECK
# ---------------------------------------------------------
@app.route("/health")
@app.route("/ping")
def health():
    return "ok", 200


# ---------------------------------------------------------
# AGGIORNAMENTO ETF (SINCRONO)
# ---------------------------------------------------------
@app.route("/api/update-all")
def update_etf():
    log_info("Richiesta /api/update-all ricevuta - avvio aggiornamento ETF SINCRONO")
    try:
        results, market_open = scraper_etf.update_all_etf()  # Esecuzione bloccante
        count = len(results) if results else 0
        log_info(f"Aggiornamento ETF completato: {count} ETF processati, market_open={market_open}")

        return jsonify({
            "status": "etf update completed",
            "updated_symbols": count,
            "market_open": market_open,
            "timestamp": datetime.now(ZoneInfo("Europe/Rome")).isoformat(),
            "results": results  # opzionale, utile per debug
        }), 200

    except Exception as e:
        # FIX: logga tipo eccezione + messaggio completo per debug preciso
        log_error(f"Errore durante aggiornamento ETF - Tipo: {type(e).__name__} - Messaggio: {e}")
        return jsonify({
            "status": "error",
            "message": f"{type(e).__name__}: {str(e)}",
            "timestamp": datetime.now(ZoneInfo("Europe/Rome")).isoformat()
        }), 500


# ---------------------------------------------------------
# FILE CSV SALVADANAIO
# ---------------------------------------------------------
@app.get("/salvadanaio.csv")
def get_csv():
    return send_from_directory("data", "salvadanaio.csv", mimetype="text/csv")


# ---------------------------------------------------------
# AGGIORNAMENTO FONDI (SINCRONO)
# ---------------------------------------------------------
@app.route("/api/update-fondi")
def update_fondi():
    log_info("Richiesta /api/update-fondi ricevuta - avvio aggiornamento fondi SINCRONO")
    try:
        scraper_fondi.main()
        log_info("Aggiornamento fondi completato con successo")

        return jsonify({
            "status": "fondi update completed",
            "timestamp": datetime.now(ZoneInfo("Europe/Rome")).isoformat()
        }), 200

    except Exception as e:
        log_error(f"Errore durante aggiornamento fondi - Tipo: {type(e).__name__} - Messaggio: {e}")
        return jsonify({
            "status": "error",
            "message": f"{type(e).__name__}: {str(e)}",
            "timestamp": datetime.now(ZoneInfo("Europe/Rome")).isoformat()
        }), 500


# ---------------------------------------------------------
# MARKET STATUS (endpoint principale, SOLO LETTURA)
# ---------------------------------------------------------
@app.route("/api/market-status")
def market_status():
    """
    Legge SOLO data/market.json scritto da scraper_etf.update_all_etf().
    Non fa scraping né aggiornamenti.
    """
    market_path = os.path.join("data", "market.json")

    now_rome = datetime.now(ZoneInfo("Europe/Rome"))
    readable = now_rome.strftime("%H:%M %d-%m-%Y")

    if not os.path.exists(market_path):
        return jsonify({
            "datetime": now_rome.isoformat(),
            "datetime_readable": readable,
            "status": "CHIUSO",
            "open": False,
            "values": {"source": "none", "data": []},
            "error": "market.json non trovato"
        }), 200

    try:
        with open(market_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        data["datetime"] = now_rome.isoformat()
        data["datetime_readable"] = readable

        return jsonify(data), 200

    except Exception as e:
        return jsonify({
            "datetime": now_rome.isoformat(),
            "datetime_readable": readable,
            "status": "CHIUSO",
            "open": False,
            "values": {"source": "error", "data": []},
            "error": f"Errore lettura market.json: {e}"
        }), 500


# ---------------------------------------------------------
# AVVIO SERVER (solo in locale)
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

# ./config.py
----------------------------------------
import pendulum

# Orari mercato LS-TC
MARKET_HOURS = {
    "timezone": "Europe/Rome",
    "open": "07:20",
    "close": "23:00"
}

# Festività italiane fisse
FIXED_HOLIDAYS = [
    (1, 1),   # Capodanno
    (4, 25),  # Liberazione
    (5, 1),   # Lavoro
    (6, 2),   # Repubblica
    (8, 15),  # Ferragosto
    (12, 25), # Natale
    (12, 26), # Santo Stefano
]

# Festività mobili (cache interna)
_cached_easter = {}

def easter_date(year):
    """Calcolo data di Pasqua (algoritmo di Meeus) con cache interna."""
    if year in _cached_easter:
        return _cached_easter[year]

    # Algoritmo di Meeus
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19*a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2*e + 2*i - h - k) % 7
    m = (a + 11*h + 22*l) // 451
    month = (h + l - 7*m + 114) // 31
    day = ((h + l - 7*m + 114) % 31) + 1

    pasqua = pendulum.date(year, month, day)
    _cached_easter[year] = pasqua
    return pasqua

def is_market_open(now=None):
    # Se non viene passato un datetime, usa quello attuale
    if now is None:
        now = pendulum.now(MARKET_HOURS["timezone"])
    else:
        now = now.in_timezone(MARKET_HOURS["timezone"])

    # Weekend (Pendulum: Monday=1 ... Sunday=7)
    if now.day_of_week in [6, 7]:  # Sabato=6, Domenica=7
        return False

    # Festività fisse
    if (now.month, now.day) in FIXED_HOLIDAYS:
        return False

    # Festività mobili
    year = now.year
    pasqua = easter_date(year)
    pasquetta = pasqua.add(days=1)
    venerdi_santo = pasqua.subtract(days=2)

    if now.date() in [pasqua, pasquetta, venerdi_santo]:
        return False

    # 24 dicembre (vigilia)
    if now.month == 12 and now.day == 24:
        return False

    # 31 dicembre (ultimo dell’anno)
    if now.month == 12 and now.day == 31:
        return False

    # Orari di apertura/chiusura
    open_hour, open_minute = map(int, MARKET_HOURS["open"].split(":"))
    close_hour, close_minute = map(int, MARKET_HOURS["close"].split(":"))

    open_time = now.replace(hour=open_hour, minute=open_minute, second=0)
    close_time = now.replace(hour=close_hour, minute=close_minute, second=0)

    return open_time <= now <= close_time


# ./Dockerfile
----------------------------------------
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Timeout alto per update lunghi
CMD ["gunicorn", "-b", "0.0.0.0:8080", "--timeout", "600", "--log-level", "info", "app:app"]

# ./etfs.json
----------------------------------------
[
  {
    "symbol": "VUAA",
    "item_id": "1045562",
    "label": "S&P 500",
    "ISIN": "IE00BFMXXD54"
  },
  {
    "symbol": "VNGA80",
    "item_id": "1376226",
    "label": "LifeStrategy 80",
    "ISIN": "IE00BMVB5R75"
  },
  {
    "symbol": "GOLD",
    "item_id": "979663",
    "label": "Physical Gold",
    "ISIN": "FR0013416716"
  },
  {
    "symbol": "XEON",
    "item_id": "58124",
    "label": "XEON",
    "ISIN": "LU0290358497"
  },
  {
    "symbol": "VWCE",
    "item_id": "1045625",
    "label": "FTSE All World",
    "ISIN": "IE00BK5BQT80"
  },
  {
    "symbol": "EXUS",
    "item_id": "3167313",
    "label": "MSCI World Ex-USA",
    "ISIN": "IE0006WW1TQ4"
  }
]

# ./fly.toml
----------------------------------------
app = "portfolio-python"
primary_region = "fra"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = "suspend"
  auto_start_machines = true
  min_machines_running = 0

  # Sintassi vecchia ma ancora perfettamente funzionante
  [http_service.concurrency]
    type = "requests"
    soft_limit = 25
    hard_limit = 50

[[vm]]
  memory = "256mb"
  cpu_kind = "shared"
  cpus = 1

[env]
  PYTHONUNBUFFERED = "1"
  TZ = "Europe/Rome"

# ./project-tree.txt
----------------------------------------
.
├── config/
│   └── variations.conf
├── data/
│   ├── fondi.csv
│   ├── fondi_nav.csv
│   ├── market.json
│   └── salvadanaio.csv
├── public/
│   ├── fondi.html
│   ├── market.html
│   ├── market-mobile.html
│   └── salvadanaio.html
├── tests/
│   ├── testDateVar.py
│   ├── testEaster.py
│   ├── test_etf.py
│   └── test_fondi.py
├── utils/
│   ├── colors.h
│   ├── holidays.py
│   └── logger.py
├── app.py
├── config.py
├── Dockerfile
├── .env
├── etfs.json
├── fly.toml
├── .gitignore
├── project-tree.txt
├── push.sh*
├── requirements.txt
├── schema.sql
├── scraper_etf.py
├── scraper_fondi.py
├── snapshot_all.sh*
└── supabase_client.py

5 directories, 31 files


# ./push.sh
----------------------------------------
#!/bin/bash
# Script per riallineare e pushare su GitHub in modo sicuro

# Vai nella cartella del progetto (relativa allo script stesso)
cd "$(dirname "$0")" || exit 1

# Determina il branch corrente
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

echo "➡️  Pull dal remoto (merge, no rebase)..."
git pull origin "$CURRENT_BRANCH" --no-rebase

# Aggiunge tutte le modifiche (nuovi, modificati, eliminati)
git add --all

# Commit fisso "fix"
git commit -m "fix" 2>/dev/null || echo "ℹ️  Nessuna modifica da commitare"

# Push sul branch corrente
echo "➡️  Push su branch: $CURRENT_BRANCH"
git push origin "$CURRENT_BRANCH"

# Deploy automatico su Fly.io
echo "🚀 Avvio deploy su Fly.io..."
fly deploy


# ./requirements.txt
----------------------------------------
flask==3.0.0
requests==2.32.3
beautifulsoup4==4.12.3
gunicorn==23.0.0
supabase==2.7.0
python-dotenv==1.0.1
python-dateutil==2.9.0.post0   # per relativedelta (usato in testDateVar e future variazioni 1m/3m)
pytest==8.3.3                 # per eseguire i test (pytest tests/)
pendulum

# ./schema.sql
----------------------------------------
-- Tabella per i valori di chiusura giornalieri degli ETF
create table if not exists previous_close (
  id bigint generated by default as identity primary key,
  symbol text not null,                -- codice ETF (es. VUAA)
  close_value numeric not null,        -- valore di chiusura
  snapshot_date date not null,         -- SOLO la data (YYYY-MM-DD)
  label text,                          -- nome leggibile dell'ETF
  inserted_at timestamptz default now()
);

-- Vincolo di unicità: un solo record per simbolo e giorno
create unique index if not exists unique_symbol_date
  on previous_close(symbol, snapshot_date);

-- Indice per query veloci per simbolo e data
create index if not exists idx_previous_close_symbol_date
  on previous_close(symbol, snapshot_date desc);


# ./scraper_etf.py
----------------------------------------
import os
import json
import base64
import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo

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
            return {"v1": "D", "v2": "W", "v3": "M", "v_led": "M"}  # fallback sicuri

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

            for key in ("v1", "v2", "v3", "v_led"):
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
        }

    save_market_json(results, market_open)
    commit_to_github()

    log_info(f"=== FINE aggiornamento ETF – {len([r for r in results.values() if r.get('status') != 'unavailable'])} ETF aggiornati ===")
    return results, market_open

# ./scraper_fondi.py
----------------------------------------
import csv
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import os
from io import StringIO
import base64

from utils.logger import log_info, log_error

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
fondi_path = os.path.join(DATA_DIR, "fondi.csv")
fondi_nav_path = os.path.join(DATA_DIR, "fondi_nav.csv")

# -----------------------------
# Fetch & Parser
# -----------------------------
def fetch_html(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.text
    except Exception as e:
        log_error(f"Errore fetch {url}: {e}")
        return None

def parse_eurizon(html):
    soup = BeautifulSoup(html, "html.parser")
    span = soup.find("span", class_="product-dashboard-token-value-bold")
    if span and span.get_text(strip=True):
        return span.get_text(strip=True)
    match = re.search(r"\d{1,3}(\.\d{3})*,\d{2}", soup.get_text())
    return match.group(0) if match else None

def parse_teleborsa(html):
    soup = BeautifulSoup(html, "html.parser")
    price_span = soup.find("span", id="ctl00_phContents_ctlHeader_lblPrice")
    if price_span and price_span.get_text(strip=True):
        return price_span.get_text(strip=True)
    alt = soup.find("span", id=re.compile(r"lblPrice", re.I))
    if alt and alt.get_text(strip=True):
        return alt.get_text(strip=True)
    match = re.search(r"\d{1,3}(\.\d{3})*,\d{2}", soup.get_text())
    return match.group(0) if match else None

def normalize(value_it):
    if not value_it:
        return None
    s = value_it.strip().replace(".", "").replace(",", ".")
    return s

# -----------------------------
# Commit GitHub
# -----------------------------
def commit_csv_to_github(path, message):
    try:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            log_info("GITHUB_TOKEN non impostato – commit saltato")
            return

        repo = "Marchino1978/portfolio"
        api_url = f"https://api.github.com/repos/{repo}/contents/{path}"

        with open(path, "rb") as f:
            content = base64.b64encode(f.read()).decode()

        sha = None
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
        resp = requests.get(api_url, headers=headers, timeout=10)
        if resp.status_code == 200:
            sha = resp.json().get("sha")

        payload = {"message": message, "content": content, "branch": "main"}
        if sha:
            payload["sha"] = sha

        put_resp = requests.put(api_url, headers=headers, json=payload, timeout=10)
        if put_resp.status_code in (200, 201):
            log_info(f"Commit GitHub OK: {path}")
        else:
            log_error(f"Errore commit GitHub: {put_resp.status_code} – {put_resp.text}")
    except Exception as e:
        log_error(f"Errore commit fondi_nav.csv: {e}")

# -----------------------------
# Main
# -----------------------------
def main():
    log_info("=== INIZIO aggiornamento fondi ===")
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(fondi_path):
        log_error(f"File fondi.csv non trovato: {fondi_path}")
        return

    with open(fondi_path, newline="", encoding="utf-8") as f:
        lines = [line for line in f if line.strip() and not line.strip().startswith("#")]

    clean_csv = StringIO("".join(lines))
    reader = csv.DictReader(clean_csv)
    reader.fieldnames = [fn.strip().lstrip("\ufeff") for fn in reader.fieldnames]

    fondi = [row for row in reader if any(row.values())]

    with open(fondi_nav_path, "w", newline="", encoding="utf-8") as f_out:
        writer = csv.writer(f_out, delimiter=";")
        writer.writerow(["timestamp", "nome", "ISIN", "nav_text_it", "nav_float"])

        for fondo in fondi:
            nome = fondo.get("nome", "").strip()
            url = fondo.get("url", "").strip()
            isin = fondo.get("ISIN", "").strip()

            if not url:
                writer.writerow([datetime.now().isoformat(), nome, isin, "NO_URL", ""])
                log_error(f"{nome} ({isin}): URL mancante")
                continue

            html = fetch_html(url)
            if "eurizoncapital.com" in url:
                nav_text = parse_eurizon(html) if html else None
            elif "teleborsa.it" in url:
                nav_text = parse_teleborsa(html) if html else None
            else:
                nav_text = None

            nav_float = normalize(nav_text)

            writer.writerow([
                datetime.now().isoformat(),
                nome,
                isin,
                nav_text or "N/D",
                nav_float or "N/D"
            ])
            status = nav_text or "N/D"
            log_info(f"{nome} ({isin}): {status}")

    commit_csv_to_github("data/fondi_nav.csv", "Update fondi_nav.csv [auto]")
    log_info("=== FINE aggiornamento fondi ===")

# ./snapshot_all.sh
----------------------------------------
#!/bin/bash
# snapshot_all.sh - genera un file .md per ogni cartella (txt/_<cartella>.md)
# Esclude: txt/, .git/, node_modules, data, public, .venv

mkdir -p txt

dump_folder() {
  local folder="$1"
  local output="txt/_$2.md"
  : > "$output"

  for file in "$folder"/*; do
    [ -f "$file" ] || continue

    echo "# $file" >> "$output"
    echo "----------------------------------------" >> "$output"

    cat "$file" >> "$output"

    echo "" >> "$output"
    echo "" >> "$output"
  done
}

# Dump della root
dump_folder "." "root"

# Dump di ogni sottocartella, esclusioni aggiornate per Python
for dir in */; do
  [ -d "$dir" ] || continue
  foldername=$(basename "$dir")
  case "$foldername" in
    txt|.git|node_modules|data|public|.venv|__pycache__) continue ;;
    *) dump_folder "$dir" "$foldername" ;;
  esac
done

echo "Snapshot .md generati in txt"

# ./supabase_client.py
----------------------------------------
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# ---------------------------------------------------------
# FACTORY: crea il client solo quando serve
# ---------------------------------------------------------
def get_supabase() -> Client:
    load_dotenv()  # sicuro, leggero, e non pesa se già chiamato
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")
    return create_client(url, key)

# ---------------------------------------------------------
# UPSERT PREVIOUS CLOSE
# ---------------------------------------------------------
def upsert_previous_close(symbol, label, close_value, snapshot_date, daily_change=None):
    supabase = get_supabase()  # <-- creato SOLO quando serve

    data = {
        "symbol": symbol,
        "label": label,
        "close_value": round(close_value, 2),
        "snapshot_date": snapshot_date,
        "daily_change": round(daily_change, 2) if daily_change is not None else None
    }

    # 1. Controllo se esiste già una riga per symbol + snapshot_date
    existing = (
        supabase.table("previous_close")
        .select("*")
        .eq("symbol", symbol)
        .eq("snapshot_date", snapshot_date)
        .execute()
    )

    # 2. Se esiste → UPDATE
    if existing.data:
        supabase.table("previous_close") \
            .update(data) \
            .eq("symbol", symbol) \
            .eq("snapshot_date", snapshot_date) \
            .execute()
    else:
        # 3. Se non esiste → INSERT
        supabase.table("previous_close") \
            .insert(data) \
            .execute()


