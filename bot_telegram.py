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
    Colori: Verde (+), Rosso (-), Bianco (0), Azzurro (N/A)
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

        # Gestione date per il titolo del report
        now = datetime.now(ZoneInfo("Europe/Rome"))
        
        nomi_mesi = [
            "DICEMBRE", "GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", 
            "GIUGNO", "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE"
        ]
        mese_index = (now.month - 1) 
        anno = now.year if now.month > 1 else now.year - 1
        
        titolo = f"📊 *REPORT ETF - {nomi_mesi[mese_index]} {anno}*\n"
        titolo += "---------------------------------------------\n\n"

        messaggio = titolo
        for etf in etfs:
            nome = etf.get("label", etf["symbol"])
            variazione_str = etf.get("v_bot", "N/A")
            prezzo = etf.get("price", 0.0)
            
            # --- LOGICA COLORI ALLINEATA A ESP32 ---
            icona = "🔵" # AZZURRO per N/A o Errori
            
            if variazione_str != "N/A":
                try:
                    # Pulizia della stringa
                    parte_numerica = variazione_str.split('%')[0]
                    val_pulito = parte_numerica.replace(',', '.').replace('+', '').strip()
                    val_num = float(val_pulito)
                    
                    if val_num > 0:
                        icona = "🟢" # VERDE per Positivo
                    elif val_num < 0:
                        icona = "🔴" # ROSSO per Negativo
                    else:
                        icona = "⚪" # BIANCO per Zero
                except Exception:
                    icona = "🔵" # AZZURRO in caso di errore conversione
            
            # Formattazione riga con icona allineata
            messaggio += f"{icona} *{nome}*\n"
            messaggio += f"   Price: €{prezzo:.2f} | Var: `{variazione_str}`\n\n"

        # Invio effettivo a Telegram
        bot.send_message(CHAT_ID, messaggio, parse_mode="Markdown")
        log_info(f"Telegram: Report mensile {nomi_mesi[mese_index]} inviato con logica colori ESP32.")

    except Exception as e:
        log_error(f"Errore durante l'invio del report Telegram: {e}")

if __name__ == "__main__":
    log_info("Avvio manuale bot_telegram.py per test...")
    send_monthly_report()
