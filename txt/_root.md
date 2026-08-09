# ./app.py
----------------------------------------
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, jsonify, send_from_directory
import os
import json

from src import scraper_etf
from src import scraper_fondi

from utils.logger import log_info, log_error

app = Flask(__name__)


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
        results, market_open = scraper_etf.main()  # Esecuzione bloccante
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
# FILE CSV SALVADANAIO E FONDI
# ---------------------------------------------------------
@app.get("/salvadanaio.csv")
def get_csv():
    return send_from_directory("data", "salvadanaio.csv", mimetype="text/csv")

@app.get("/fondi.csv")
def get_fondi_csv():
    return send_from_directory("data", "fondi.csv", mimetype="text/csv")


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
    Legge SOLO data/market.json scritto da scraper_etf.main().
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
├── backup_SQL/
│   ├── backup_supabase_2026_07_20.sql
│   ├── backup_supabase_2026_07_27.sql
│   └── backup_supabase_2026_08_03.sql
├── config/
│   ├── schema.sql
│   └── variations.conf
├── data/
│   ├── etfs.json
│   ├── fondi.csv
│   ├── fondi_nav.csv
│   ├── market.json
│   ├── money.csv
│   └── salvadanaio.csv
├── esp32/
│   ├── case.stl
│   ├── config.example.h
│   ├── config.h
│   ├── ETF.example.ino
│   └── ETF.ino
├── gallery/
│   ├── case.gif
│   ├── case.png
│   ├── coin counter.png
│   ├── ETF charts.png
│   ├── MARKET live [close].png
│   ├── report_annuale.png
│   ├── report_mensile.png
│   └── splash.png
├── old/
│   ├── fondi.html
│   ├── index.html
│   ├── market.html
│   └── market-mobile.html
├── public/
│   ├── ETF charts.html
│   ├── MARKET live.html
│   ├── money.html
│   └── salvadanaio.html
├── scripts/
│   ├── push.sh*
│   └── snapshot_all.sh*
├── src/
│   ├── backup_manager.py
│   ├── bot_telegram.py
│   ├── check_alert.py
│   ├── config.py
│   ├── __init__.py
│   ├── report_annuale.py
│   ├── scraper_etf.py
│   ├── scraper_fondi.py
│   └── supabase_client.py
├── tests/
│   ├── testDateVar.py
│   └── testEaster.py
├── utils/
│   ├── colors.h
│   ├── holidays.py
│   ├── __init__.py
│   └── logger.py
├── app.py
├── Dockerfile
├── .env
├── fly.toml
├── .gitignore
├── project-tree.txt
├── README.md
└── requirements.txt

11 directories, 57 files


# ./README.md
----------------------------------------
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:00c6ff,100:0072ff&fontColor=FFD700&height=100&section=header&text=PORTFOLIO%20TRACKER&fontSize=50"
  alt="PORTFOLIO TRACKER - Financial market dashboard, Telegram bot report, Alexa notifications, ESP32-C6 Waveshare 1.47 display, Python web-scraping, GitHub, Supabase, Fly.io, Raspberry Pi 400, CSV, HTML" />
</p>

<div align="center">

This project was born after Yahoo Finance discontinued its free API service for downloading market data into my spreadsheets.
<br><br>
Instead of switching to a paid service, I decided to build my own solution using PYTHON, free services and an ESP32 display.
<br><br>
Today it collects market data via web scraping, stores historical records in a SUPABASE PostgreSQL database, and updates JSON feeds on GITHUB — acting as the central data hub for the web dashboard, the ESP32 display, and spreadsheets. It also generates TELEGRAM reports and drives ALEXA notifications with SMART LIGHT control — all running on free-tier services.

</div>

<p align="center">
  <img src="gallery/splash.png" alt="ESP32-C6 smart home and financial dashboard showing market charts, voice assistant notifications, and smart light control" width="600">
</p>

<p align="center">
  <strong>Developed on Raspberry Pi 400 | Hosted on Fly.io | Uptime: running since Dec 2025</strong>
</p>


# ./requirements.txt
----------------------------------------
flask==3.0.0
requests==2.32.3
beautifulsoup4==4.12.3
gunicorn==23.0.0
supabase==2.7.0
python-dotenv==1.0.1
python-dateutil==2.9.0.post0
pytest==8.3.3
pendulum
pyTelegramBotAPI


