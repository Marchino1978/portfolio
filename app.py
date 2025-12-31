from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, jsonify, send_from_directory
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
# AGGIORNAMENTO ETF (SINCRONO)
# ---------------------------------------------------------
@app.route("/api/update-all")
def update_etf():
    results, market_open = scraper_etf.update_all_etf()   # <-- SINCRONO
    return jsonify({
        "status": "etf update completed",
        "market_open": market_open
    })


# ---------------------------------------------------------
# FILE CSV SALVADANAIO
# ---------------------------------------------------------
@app.get("/salvadanaio.csv")
def get_csv():
    return send_from_directory("data", "salvadanaio.csv", mimetype="text/csv")


# ---------------------------------------------------------
# AGGIORNAMENTO FONDI (SINCRONO, COME ETF)
# ---------------------------------------------------------
@app.route("/api/update-fondi")
def update_fondi():
    scraper_fondi.main()   # <-- SINCRONO
    return jsonify({"status": "fondi update completed"})


# ---------------------------------------------------------
# MARKET STATUS (endpoint principale, SOLO LETTURA)
# ---------------------------------------------------------
@app.route("/api/market-status")
def market_status():
    market_path = os.path.join("data", "market.json")

    if not os.path.exists(market_path):
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
