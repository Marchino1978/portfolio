import os
import json
from datetime import datetime
import telebot
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from utils.logger import log_info, log_error

# Carica le variabili dal file .env (per sicurezza sul server)
load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Inizializza il bot
bot = telebot.TeleBot(TOKEN)

def send_monthly_report():
    """
    Invia il report basato sui valori v_bot presenti in market.json
    """
    # Costruisce il percorso del file market.json (cartella data nella root)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    market_path = os.path.join(base_dir, "data", "market.json")
    
    if not os.path.exists(market_path):
        log_error(f"Bot Telegram: file non trovato in {market_path}")
        return

    try:
        with open(market_path, "r", encoding="utf-8") as f:
            market_data = json.load(f)
        
        etfs = market_data.get("values", {}).get("data", [])
        if not etfs:
            log_error("Bot Telegram: Nessun dato ETF trovato nel JSON.")
            return

        # Gestione date per il titolo del report (riferito al mese appena concluso)
        now = datetime.now(ZoneInfo("Europe/Rome"))
        
        # Se oggi è il 1 Febbraio, il report è relativo a GENNAIO
        nomi_mesi = [
            "DICEMBRE", "GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", 
            "GIUGNO", "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE"
        ]
        # Se siamo a Gennaio (1), l'indice punterà a Dicembre (0) dell'anno prima
        mese_index = (now.month - 1) 
        anno = now.year if now.month > 1 else now.year - 1
        
        titolo = f"📊 *REPORT ETF - {nomi_mesi[mese_index]} {anno}*\n"
        titolo += f"Variazione Periodo (`v_bot`)\n"
        titolo += "---------------------------\n\n"

        messaggio = titolo
        for etf in etfs:
            nome = etf.get("label", etf["symbol"])
            variazione = etf.get("v_bot", "N/A")
            prezzo = etf.get("price", 0.0)
            
            # Formattazione riga: Nome ETF in grassetto, variazioni in codice
            messaggio += f"🔹 *{nome}*\n"
            messaggio += f"   Ultimo: €{prezzo:.2f} | Var: `{variazione}`\n\n"

        # Invio effettivo a Telegram
        bot.send_message(CHAT_ID, messaggio, parse_mode="Markdown")
        log_info(f"Telegram: Report mensile {nomi_mesi[mese_index]} inviato a CHAT_ID {CHAT_ID}")

    except Exception as e:
        log_error(f"Errore durante l'invio del report Telegram: {e}")

if __name__ == "__main__":
    # Se lo lanci a mano (python bot_telegram.py), invia un test
    log_info("Avvio manuale bot_telegram.py per test...")
    send_monthly_report()
