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
def market():
    return send_from_directory("public", "market.html")

@app.route("/")
def market_mobile():
    return send_from_directory("public", "market-mobile.html")

@app.route("/")
def salvadanaio():
    return send_from_directory("public", "salvadanaio.html")

@app.route("/")
def fondi():
    return send_from_directory("public", "fondi.html")

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