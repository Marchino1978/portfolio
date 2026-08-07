import os
import json
from datetime import datetime
import telebot
from zoneinfo import ZoneInfo
from supabase_client import get_supabase
from utils.logger import log_info, log_error
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = telebot.TeleBot(TOKEN)

def genera_grafico_e_report(is_test=False):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    market_path = os.path.join(base_dir, "data", "market.json")

    if not os.path.exists(market_path):
        log_error("Report Annuale: market.json locale non trovato.")
        return

    try:
        with open(market_path, "r", encoding="utf-8") as f:
            market_data = json.load(f)
        etfs = market_data.get("values", {}).get("data", [])
        if not etfs: return

        anno_corrente = datetime.now(ZoneInfo("Europe/Rome")).year
        anno_precedente = anno_corrente if is_test else anno_corrente - 1
        
        data_inizio_query = "2025-12-01" if is_test else f"{anno_precedente}-01-01"
        data_fine_query = "2026-12-31" if is_test else f"{anno_precedente}-12-31"
        
        testo_report = f"📊 *REPORT ANNO {anno_precedente}*\n"
        testo_report += "```\n" 

        supabase = get_supabase()
        inviato = False

        for etf in etfs:
            symbol = etf["symbol"]
            prezzo_attuale = float(etf.get("price", 0.0))

            response = (
                supabase.table("previous_close")
                .select("close_value")
                .eq("symbol", symbol)
                .filter("snapshot_date", "gte", data_inizio_query)
                .filter("snapshot_date", "lte", data_fine_query)
                .order("snapshot_date", desc=False)
                .limit(1)
                .execute()
            )

            if not response.data:
                continue

            prezzo_inizio = float(response.data[0]['close_value'])
            variazione_annuale = ((prezzo_attuale - prezzo_inizio) / prezzo_inizio) * 100
            
            segno = "+" if variazione_annuale > 0 else ""
            var_str = f"{segno}{variazione_annuale:.1f}%"
            
            num_quadrati = min(int(abs(variazione_annuale) / 3.5), 5)
            if num_quadrati == 0 and variazione_annuale != 0: 
                num_quadrati = 1 
                
            if variazione_annuale > 0:
                grafico_barre = "     ┃" + "🟩" * num_quadrati
            elif variazione_annuale < 0:
                grafico_barre = f"{'🟥' * num_quadrati:>5}┃"
            else:
                grafico_barre = "     ┃"

            testo_report += f"{symbol:<7} {var_str:<7} {grafico_barre}\n"
            inviato = True

        testo_report += "```" 

        if inviato:
            bot.send_message(CHAT_ID, testo_report, parse_mode="Markdown")
            log_info(f"Report annuale testuale per il {anno_precedente} inviato su Telegram.")
        else:
            log_error("Report Annuale: Nessun dato trovato con i filtri impostati.")

    except Exception as e:
        log_error(f"Errore generazione report annuale: {e}")

if __name__ == "__main__":
    genera_grafico_e_report(is_test=True)
