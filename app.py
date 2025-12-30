from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, jsonify, send_from_directory
import threading

# Import dei moduli (NON delle funzioni)
import scraper_etf
import scraper_fondi
from config import is_market_open

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
# AGGIORNAMENTO FONDI (async)
# ---------------------------------------------------------
@app.route("/api/update-fondi")
def update_fondi():
    threading.Thread(target=scraper_fondi.main).start()
    return jsonify({"status": "fondi update started"})


# ---------------------------------------------------------
# MARKET STATUS (endpoint principale)
# ---------------------------------------------------------
@app.route("/api/market-status")
def market_status():
    # Eseguito in modo sincrono per risposta immediata
    results, market_open = scraper_etf.update_all_etf()

    data = []
    for symbol, info in results.items():
        data.append({
            "symbol": symbol,
            "label": info.get("label", symbol),
            "price": info.get("price"),
            "previousClose": info.get("previous_close"),
            "dailyChange": info.get("daily_change"),
            "snapshotDate": info.get("snapshot_date"),
            "status": info.get("status", "unavailable")
        })

    # Ora in fuso orario Europe/Rome + formato leggibile
    now_rome = datetime.now(ZoneInfo("Europe/Rome"))
    readable = now_rome.strftime("%H:%M %d-%m-%Y")

    return jsonify({
        "datetime": now_rome.isoformat(),
        "datetime_readable": readable,
        "status": "APERTO" if market_open else "CHIUSO",
        "open": market_open,
        "values": {"source": "live", "data": data}
    })


# ---------------------------------------------------------
# AVVIO SERVER
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
