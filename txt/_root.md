# ./app.py
----------------------------------------
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, jsonify, send_from_directory
import threading
import os
import json

# Import dei moduli (NON delle funzioni)
import scraper_etf
import scraper_fondi

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
# AGGIORNAMENTO ETF (async)
# ---------------------------------------------------------
@app.route("/api/update-all")
def update_etf():
    threading.Thread(target=scraper_etf.update_all_etf).start()
    return jsonify({"status": "etf update started"})


# ---------------------------------------------------------
# FILE CSV SALVADANAIO
# ---------------------------------------------------------
@app.get("/salvadanaio.csv")
def get_csv():
    return send_from_directory("data", "salvadanaio.csv", mimetype="text/csv")


# ---------------------------------------------------------
# AGGIORNAMENTO FONDI (UNIFORME, SENZA THREAD)
# ---------------------------------------------------------
@app.route("/api/update-fondi")
def update_fondi():
    scraper_fondi.main()   # <-- ESECUZIONE DIRETTA, COME ETF NEL PROCESSO PRINCIPALE
    return jsonify({"status": "fondi update completed"})


# ---------------------------------------------------------
# MARKET STATUS (endpoint principale, SOLO LETTURA)
# ---------------------------------------------------------
@app.route("/api/market-status")
def market_status():
    """
    NON fa scraping.
    NON chiama update_all_etf.
    Legge SOLO data/market.json scritto da scraper_etf.update_all_etf().
    """

    market_path = os.path.join("data", "market.json")

    if not os.path.exists(market_path):
        # Nessun dato ancora disponibile
        now_rome = datetime.now(ZoneInfo("Europe/Rome"))
        readable = now_rome.strftime("%H:%M %d-%m-%Y")
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

        # Aggiungo solo timestamp lato server per coerenza
        now_rome = datetime.now(ZoneInfo("Europe/Rome"))
        readable = now_rome.strftime("%H:%M %d-%m-%Y")

        data["datetime"] = now_rome.isoformat()
        data["datetime_readable"] = readable

        return jsonify(data), 200

    except Exception as e:
        now_rome = datetime.now(ZoneInfo("Europe/Rome"))
        readable = now_rome.strftime("%H:%M %d-%m-%Y")
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
    #if now.month == 12 and now.day == 31:
        #return False

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
CMD ["gunicorn", "-b", "0.0.0.0:8080", "--timeout", "180", "app:app"]


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
app = "portfolio-phyton"
primary_region = "fra"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = "suspend"
  auto_start_machines = true
  min_machines_running = 0

[[vm]]
  memory = "512mb"
  cpu_kind = "shared"
  cpus = 1

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

HEADERS = {"User-Agent": "Mozilla/5.0"}

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
        with open(path, "r") as f:
            return json.load(f)
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
            return config

        with open(path, "r") as f:
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
# PREVIOUS CLOSE
# ---------------------------------------------------------
def get_previous_close(symbol, supabase):
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
# VARIAZIONI MULTI-PERIODO
# ---------------------------------------------------------
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

        log_info(f"[WARN] Nessun prezzo storico trovato per {symbol} fino a {target_str}")
        return None
    except Exception as e:
        log_error(f"Errore get_price_on_or_before({symbol}, {target_date}): {e}")
        return None

def calc_variation(price_today, price_past):
    if price_today is None or price_past is None:
        return None
    try:
        return ((price_today - price_past) / price_past) * 100.0
    except ZeroDivisionError:
        return None

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

            for key in ("v1", "v2", "v3", "v_led"):
                if key in etf:
                    entry[key] = etf[key]

            data_array.append(entry)

        json_output = {
            "status": "APERTO" if market_open else "CHIUSO",
            "values": {"data": data_array},
            "last_updated": {
                "iso": now.isoformat(),
                "readable": readable
            }
        }

        with open(path, "w") as f:
            json.dump(json_output, f, indent=2, ensure_ascii=False)

        log_info(f"market.json aggiornato in {path}")

    except Exception as e:
        log_error(f"Errore salvataggio market.json: {e}")

# ---------------------------------------------------------
# COMMIT GITHUB (CON TIMEOUT)
# ---------------------------------------------------------
def commit_to_github():
    try:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            log_error("GITHUB_TOKEN non impostato")
            return

        repo = "Marchino1978/portfolio"
        path = "data/market.json"
        api_url = f"https://api.github.com/repos/{repo}/contents/{path}"

        with open(path, "rb") as f:
            content = f.read()

        encoded = base64.b64encode(content).decode("utf-8")

        sha = None
        get_resp = requests.get(
            api_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json"
            },
            timeout=10
        )

        if get_resp.status_code == 200:
            sha = get_resp.json().get("sha")

        payload = {
            "message": "Update market.json",
            "content": encoded,
            "branch": "main"
        }

        if sha:
            payload["sha"] = sha

        put_resp = requests.put(
            api_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json"
            },
            json=payload,
            timeout=10
        )

        if put_resp.status_code in (200, 201):
            log_info("Commit su GitHub completato")
        else:
            log_error(f"Errore GitHub API: {put_resp.status_code} - {put_resp.text}")

    except Exception as e:
        log_error(f"Errore commit GitHub API: {e}")

# ---------------------------------------------------------
# FUNZIONE PRINCIPALE
# ---------------------------------------------------------
def update_all_etf():
    today_date = date.today()
    today_str = today_date.isoformat()
    market_open = is_market_open()

    supabase = get_supabase()

    ETFS = load_etfs()
    variation_config = load_variation_config()

    results = {}

    for etf in ETFS:
        symbol = etf["symbol"]
        label = etf["label"]

        price = scrape_price(etf["item_id"])
        if price is None:
            results[symbol] = {"status": "unavailable"}
            continue

        prev = get_previous_close(symbol, supabase)

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

        all_variations = compute_all_variations(symbol, price, today_date, supabase)

        v1_code = variation_config.get("v1", "D")
        v2_code = variation_config.get("v2", "W")
        v3_code = variation_config.get("v3", "M")
        v_led_code = variation_config.get("v_led", "M")

        results[symbol] = {
            "symbol": symbol,
            "label": label,
            "price": price,
            "previous_close": prev,
            "daily_change": daily_change,
            "snapshot_date": today_str,
            "status": "open" if market_open else "closed",
            "v1": all_variations.get(v1_code, "N/A"),
            "v2": all_variations.get(v2_code, "N/A"),
            "v3": all_variations.get(v3_code, "N/A"),
            "v_led": all_variations.get(v_led_code, "N/A"),
        }

    log_info(f"Aggiornamento ETF completato: {len(results)} simboli")

    save_market_json(results, market_open)
    commit_to_github()

    return results, market_open


# ./scraper_fondi.py
----------------------------------------
import csv
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import os
from io import StringIO  # Per ricostruire il CSV pulito
import base64  # per commit GitHub

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# -----------------------------
# Percorsi robusti
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

fondi_path = os.path.join(DATA_DIR, "fondi.csv")
fondi_nav_path = os.path.join(DATA_DIR, "fondi_nav.csv")

# -----------------------------
# Fetch HTML con gestione errori
# -----------------------------
def fetch_html(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        if not r.text or len(r.text.strip()) == 0:
            raise ValueError("HTML vuoto da " + url)
        return r.text
    except Exception as e:
        print(f"Errore fetch {url}: {e}")
        return None

# -----------------------------
# Parser Eurizon
# -----------------------------
def parse_eurizon(html):
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    span = soup.find("span", class_="product-dashboard-token-value-bold color-green")
    if span and span.get_text(strip=True):
        return span.get_text(strip=True)
    text = soup.get_text(" ", strip=True)
    match = re.search(r"\b\d{1,3}(\.\d{3})*,\d{2}\b|\b\d+,\d{2}\b", text)
    if match:
        return match.group(0)
    return None

# -----------------------------
# Parser Teleborsa
# -----------------------------
def parse_teleborsa(html):
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    price_span = soup.find("span", id="ctl00_phContents_ctlHeader_lblPrice")
    if price_span:
        raw = price_span.get_text(strip=True)
        if raw:
            return raw
    alt = soup.find("span", id=re.compile(r"lblPrice", re.I))
    if alt:
        raw = alt.get_text(strip=True)
        if raw:
            return raw
    text = soup.get_text(" ", strip=True)
    match = re.search(r"\b\d{1,3}(\.\d{3})*,\d{2}\b|\b\d{1,3}(\.\d{3})*\b", text)
    if match:
        return match.group(0)
    return None

# -----------------------------
# Normalizzazione valori IT -> EN
# -----------------------------
def normalize(value_it):
    if not value_it:
        return None
    s = value_it.strip()
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(".", "")
    return s

# -----------------------------
# Commit CSV su GitHub (CON TIMEOUT)
# -----------------------------
def commit_csv_to_github(path, message):
    try:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            print("GITHUB_TOKEN non impostato")
            return

        repo = "Marchino1978/portfolio"
        api_url = f"https://api.github.com/repos/{repo}/contents/{path}"

        with open(path, "rb") as f:
            content = f.read()

        encoded = base64.b64encode(content).decode("utf-8")

        sha = None
        get_resp = requests.get(
            api_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json"
            },
            timeout=10
        )
        if get_resp.status_code == 200:
            sha = get_resp.json().get("sha")

        payload = {
            "message": message,
            "content": encoded,
            "branch": "main"
        }
        if sha:
            payload["sha"] = sha

        put_resp = requests.put(
            api_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json"
            },
            json=payload,
            timeout=10
        )

        if put_resp.status_code in (200, 201):
            print(f"Commit GitHub OK: {path}")
        else:
            print(f"Errore GitHub {path}: {put_resp.status_code} - {put_resp.text}")

    except Exception as e:
        print(f"Errore commit CSV {path}: {e}")

# -----------------------------
# Main di aggiornamento fondi
# -----------------------------
def main():
    fondi = []
    with open(fondi_path, newline="", encoding="utf-8") as f:
        lines = f.readlines()

    clean_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        clean_lines.append(line)

    clean_csv = StringIO("".join(clean_lines))
    reader = csv.DictReader(clean_csv)

    if reader.fieldnames:
        reader.fieldnames = [fn.strip().lstrip("\ufeff") for fn in reader.fieldnames]

    for row in reader:
        clean_row = {k.strip(): v.strip() for k, v in row.items() if k is not None}
        if not any(clean_row.values()):
            continue
        fondi.append(clean_row)

    with open(fondi_nav_path, "w", newline="", encoding="utf-8") as f_out:
        writer = csv.writer(f_out, delimiter=";")
        writer.writerow(["timestamp", "nome", "ISIN", "nav_text_it", "nav_float"])

        for fondo in fondi:
            nome = fondo.get("nome", "")
            url = fondo.get("url", "")
            isin = fondo.get("ISIN", "")
            try:
                html = fetch_html(url)
                if not html:
                    raise ValueError("HTML non disponibile")

                if "eurizoncapital.com" in url:
                    nav_text = parse_eurizon(html)
                elif "teleborsa.it" in url:
                    nav_text = parse_teleborsa(html)
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
                print(f"{nome} ({isin}): {nav_text or 'N/D'}")

            except Exception as e:
                writer.writerow([datetime.now().isoformat(), nome, isin, "ERRORE", ""])
                print(f"{nome} ({isin}): errore {repr(e)}")

    commit_csv_to_github("data/fondi_nav.csv", "Update fondi_nav.csv")


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


