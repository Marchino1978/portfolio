import os
import json
from datetime import datetime
import pandas as pd

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

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
    grafico_path = os.path.join(base_dir, "data", "rendimento_annuale.png")

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
        
        titolo_testo = "TEST GRAFICO" if is_test else f"{anno_precedente}"
        testo_report = f"🏆 *BILANCIO INVESTIMENTI ANNUALE - {titolo_testo}*\n"
        testo_report += "--------------------------------------------------\n\n"
        
        nomi_etf = []
        rendimenti = []
        colori_barre = []

        supabase = get_supabase()

        for etf in etfs:
            symbol = etf["symbol"]
            nome = etf.get("label", symbol)
            prezzo_attuale = float(etf.get("price", 0.0))

            response = (
                supabase.table("previous_close")
                .select("close_value, snapshot_date")
                .eq("symbol", symbol)
                .filter("snapshot_date", "gte", f"{anno_precedente}-01-01")
                .filter("snapshot_date", "lte", f"{anno_precedente}-12-31")
                .order("snapshot_date", desc=False)
                .execute()
            )

            if not response.data:
                continue

            df = pd.DataFrame(response.data)
            prezzo_inizio = float(df.iloc[0]['close_value'])
            
            variazione_annuale = ((prezzo_attuale - prezzo_inizio) / prezzo_inizio) * 100
            
            icona = "🟢" if variazione_annuale > 0 else "🔴" if variazione_annuale < 0 else "⚪"
            segno = "+" if variazione_annuale > 0 else ""
            
            testo_report += f"{icona} *{nome}*\n"
            testo_report += f"   Inizio: €{prezzo_inizio:.2f} ➔ Attuale: €{prezzo_attuale:.2f}\n"
            testo_report += f"   Rendimento: `{segno}{variazione_annuale:.2f}%`\n\n"

            nomi_etf.append(nome)
            rendimenti.append(variazione_annuale)
            colori_barre.append("#2ecc71" if variazione_annuale > 0 else "#e74c3c")

        if rendimenti:
            fig, ax = plt.subplots(figsize=(10, len(nomi_etf) * 0.8 + 2))
            fig.patch.set_facecolor('#0a0a0a')
            ax.set_facecolor('#111111')

            barre = ax.barh(nomi_etf, rendimenti, color=colori_barre, edgecolor="black", height=0.5)
            
            max_val = max(abs(x) for x in rendimenti)
            limite_x = max_val + 3
            ax.set_xlim(-limite_x, limite_x)
            
            ax.axvline(0, color="white", linestyle="-", linewidth=1.5, alpha=0.7)
            
            ax.set_title(f"Rendimento % ETF - {titolo_testo}", color="white", fontsize=14, fontweight='bold', pad=15)
            ax.tick_params(colors="gray", labelsize=10)
            ax.grid(axis='x', linestyle=':', color="#222222", alpha=0.5)
            
            for spine in ax.spines.values():
                spine.set_visible(False)
            
            for barra in barre:
                width = barra.get_width()
                if width >= 0:
                    ax.text(width + 0.3, barra.get_y() + barra.get_height()/2, f'+{width:.2f}%', 
                            va='center', ha='left', color='#2ecc71', fontweight='bold', fontsize=10)
                else:
                    ax.text(width - 0.3, barra.get_y() + barra.get_height()/2, f'{width:.2f}%', 
                            va='center', ha='right', color='#e74c3c', fontweight='bold', fontsize=10)
            
            plt.tight_layout()
            plt.savefig(grafico_path, dpi=200, facecolor=fig.get_facecolor(), edgecolor='none')
            plt.close()

            with open(grafico_path, "rb") as foto:
                bot.send_photo(CHAT_ID, foto, caption=testo_report, parse_mode="Markdown")
            
            log_info("Report annuale inviato su Telegram.")
            
            if os.path.exists(grafico_path):
                os.remove(grafico_path)
        else:
            log_error("Report Annuale: Nessun dato trovato nella tabella previous_close.")

    except Exception as e:
        log_error(f"Errore generazione report annuale grafico: {e}")

if __name__ == "__main__":
    print("Avvio manuale report_annuale.py per test...")
    genera_grafico_e_report(is_test=True)
