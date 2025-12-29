from datetime import datetime
from flask import Flask, jsonify, send_from_directory, Response
from scraper_etf import update_all_etf
from scraper_fondi import main as scrape_fondi
from config import is_market_open
import threading

app = Flask(__name__, static_folder="public", static_url_path="")

@app.route("/")
def index():
    return send_from_directory("public", "market.html")

@app.route("/market-mobile")
def market_mobile():
    return send_from_directory("public", "market-mobile.html")

@app.route("/salvadanaio")
def salvadanaio():
    return send_from_directory("public", "salvadanaio.html")

@app.route("/health")
@app.route("/ping")
def health():
    return "ok", 200

@app.route("/api/update-all")
def update_etf():
    threading.Thread(target=update_all_etf).start()
    return jsonify({"status": "etf update started"})

@app.get("/salvadanaio.csv")
def get_csv():
    return send_from_directory("data", "salvadanaio.csv", mimetype="text/csv")

@app.route("/update-fondi")
def update_fondi():
    threading.Thread(target=scrape_fondi).start()
    return jsonify({"status": "fondi update started"})

@app.route("/api/market-status")
def market_status():
    results, market_open = update_all_etf()  # sync per risposta immediata

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

    return jsonify({
        "datetime": datetime.now().isoformat(),
        "status": "APERTO" if market_open else "CHIUSO",
        "open": market_open,
        "values": {"source": "live", "data": data}
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
