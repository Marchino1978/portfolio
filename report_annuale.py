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

        # Se è un test partiamo da dicembre 2025 (i tuoi primi dati), altrimenti calcola l'anno scorso
        data_inizio_query = "2025-12-01" if is_test else f"{datetime.now(ZoneInfo('Europe/Rome')).year - 1}-01-01"
        data_fine_query = "2026-12-31" if is_test else f"{datetime.now(ZoneInfo('Europe/Rome')).year - 1}-12-31"
        
        titolo_testo = "STORICO COMPLETO (da Dic 25)" if is_test else f"ANNO {datetime.now(ZoneInfo('Europe/Rome')).year - 1}"
        
        testo_report = f"🏆 *BILANCIO INVESTIMENTI - {titolo_testo}*\n"
        testo_report += "```\n"

        supabase = get_supabase()
        inviato = False

        for etf in etfs:
            symbol = etf["symbol"]
            nome = etf.get("label", symbol)[:10] # Prende i primi 10 caratteri del nome per non sballare le colonne
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
            
            # --- LOGICA DEL GRAFICO CON LO ZERO AL CENTRO (Max 5 quadratini per lato) ---
            num_quadrati = min(int(abs(variazione_annuale) / 3), 5) # 1 quadratino ogni 3% di variazione
            if num_quadrati == 0 and variazione_annuale != 0: 
                num_quadrati = 1 # Almeno un quadratino se c'è movimento
                
            if variazione_annuale > 0:
                # Guadagno: spazio vuoto a sinistra, linea al centro, quadratini verdi a destra
                grafico_barre = "     ┃" + "🟩" * num_quadrati
            elif variazione_annuale < 0:
                # Perdita: quadratini rossi a sinistra allineati a destra, linea al centro
                grafico_barre = f"{'🟥' * num_quadrati:>5}┃"
            else:
                # Zero spaccato
                grafico_barre = "     ┃"

            # Allinea il nome a sinistra (10 spazi) e la percentuale (6 spazi)
            testo_report += f"{nome:<10} {var_str:<6} {grafico_barre}\n"
            inviato = True

        testo_report += "```" # Chiude il blocco monospazio

        if inviato:
            bot.send_message(CHAT_ID, testo_report, parse_mode="Markdown")
            log_info("Report annuale testuale grafico inviato su Telegram.")
        else:
            log_error("Report Annuale: Nessun dato trovato con i filtri impostati.")

    except Exception as e:
        log_error(f"Errore generazione report annuale: {e}")

if __name__ == "__main__":
    genera_grafico_e_report(is_test=True)
