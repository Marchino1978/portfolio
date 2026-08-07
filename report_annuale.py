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
        
        titolo_testo = "TEST STORICO" if is_test else f"{anno_precedente}"
        
        # Costruzione del testo con una barra grafica testuale ad alta leggibilità
        testo_report = f"🏆 *BILANCIO INVESTIMENTI ANNUALE - {titolo_testo}*\n"
        testo_report += "==================================\n\n"

        supabase = get_supabase()
        inviato = False

        for etf in etfs:
            symbol = etf["symbol"]
            nome = etf.get("label", symbol)
            prezzo_attuale = float(etf.get("price", 0.0))

            response = (
                supabase.table("previous_close")
                .select("close_value")
                .eq("symbol", symbol)
                .filter("snapshot_date", "gte", f"{anno_precedente}-01-01")
                .filter("snapshot_date", "lte", f"{anno_precedente}-12-31")
                .order("snapshot_date", desc=False)
                .limit(1)
                .execute()
            )

            if not response.data:
                continue

            prezzo_inizio = float(response.data[0]['close_value'])
            variazione_annuale = ((prezzo_attuale - prezzo_inizio) / prezzo_inizio) * 100
            
            icona = "🟢" if variazione_annuale > 0 else "🔴" if variazione_annuale < 0 else "⚪"
            segno = "+" if variazione_annuale > 0 else ""
            
            # Creiamo una barretta visiva usando i caratteri di testo (es. ▬▬▬)
            num_quadrati = min(int(abs(variazione_annuale) / 2), 10)
            barra_visiva = "▬" * num_quadrati if num_quadrati > 0 else "▬"
            freccia = "▶" if variazione_annuale >= 0 else "◀"
            
            testo_report += f"{icona} *{nome}*\n"
            testo_report += f"  • Inizio: €{prezzo_inizio:.2f} ➔ Fine: €{prezzo_attuale:.2f}\n"
            testo_report += f"  • Rendimento: `{segno}{variazione_annuale:.2f}%`\n"
            testo_report += f"  • Grafico: 0% {freccia}{barra_visiva}\n\n"
            inviato = True

        if inviato:
            testo_report += "=================================="
            bot.send_message(CHAT_ID, testo_report, parse_mode="Markdown")
            log_info("Report annuale testuale inviato con successo.")
        else:
            log_error("Report Annuale: Nessun dato trovato nella tabella previous_close.")

    except Exception as e:
        log_error(f"Errore generazione report annuale testuale: {e}")

if __name__ == "__main__":
    genera_grafico_e_report(is_test=True)
