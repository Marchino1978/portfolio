# src//backup_manager.py
----------------------------------------
import os
import base64
import requests
from datetime import datetime
from src.supabase_client import get_supabase
from utils.logger import log_info, log_error

def run_supabase_backup():
    table_name = "previous_close"
    folder = "backup_SQL"
    filename = f"backup_supabase_{datetime.now().strftime('%Y_%m_%d')}.sql"
    file_path = os.path.join(folder, filename)
    
    log_info(f"Inizio generazione backup SQL: {filename}")
    
    try:
        # Recupero dati da Supabase
        supabase = get_supabase()
        resp = supabase.table(table_name).select("*").order("snapshot_date", desc=True).execute()
        rows = resp.data
        if not rows: 
            return None
        
        os.makedirs(folder, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"-- BACKUP AUTOMATICO: {table_name}\n\n")
            f.write(f"TRUNCATE TABLE {table_name};\n\n")
            
            for row in rows:
                cols = ", ".join(row.keys())
                
                vals_list = []
                for v in row.values():
                    if v is None:
                        vals_list.append("NULL")
                    elif isinstance(v, (int, float)):
                        vals_list.append(str(v))
                    else:
                        # Raddoppia gli apici per SQL e avvolge tra apici singoli
                        safe_v = str(v).replace("'", "''")
                        vals_list.append(f"'{safe_v}'")
                
                vals_string = ", ".join(vals_list)
                f.write(f"INSERT INTO {table_name} ({cols}) VALUES ({vals_string});\n")
                # ----------------------------------
        
        log_info(f"Backup locale completato: {file_path}")
        return file_path
    except Exception as e:
        log_error(f"Errore generazione backup: {e}")
        return None

def upload_backup_to_github(file_path):
    """Carica il backup e mantiene solo gli ultimi 3 file nella cartella backup_SQL."""
    token = os.environ.get("GITHUB_TOKEN")
    repo = "Marchino1978/portfolio"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    
    file_name = os.path.basename(file_path)
    api_url_base = f"https://api.github.com/repos/{repo}/contents/backup_SQL"
    
    try:
        with open(file_path, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf-8")
        
        put_resp = requests.put(f"{api_url_base}/{file_name}", headers=headers, json={
            "message": "fix",
            "content": content,
            "branch": "main"
        }, timeout=10)
        
        if put_resp.status_code in [200, 201]:
            log_info(f"Nuovo backup {file_name} caricato in backup_SQL.")
        else:
            log_error(f"Errore upload GitHub: {put_resp.text}")

        # Rotazione backup (ne tiene 3)
        resp = requests.get(api_url_base, headers=headers, timeout=10)
        if resp.status_code == 200:
            files = resp.json()
            backups = sorted([f for f in files if f['name'].endswith(".sql")], 
                            key=lambda x: x['name'], reverse=True)

            if len(backups) > 3:
                for old_file in backups[3:]:
                    del_url = f"https://api.github.com/repos/{repo}/contents/{old_file['path']}"
                    requests.delete(del_url, headers=headers, json={
                        "message": "fix",
                        "sha": old_file['sha'],
                        "branch": "main"
                    }, timeout=10)
                    log_info(f"Rimosso vecchio backup da GitHub: {old_file['name']}")

    except Exception as e:
        log_error(f"Errore durante rotazione backup su GitHub: {e}")

if __name__ == "__main__":
    path = run_supabase_backup()
    if path: 
        upload_backup_to_github(path)

# src//bot_telegram.py
----------------------------------------
import os
import json
from datetime import datetime
import telebot
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from utils.logger import log_info, log_error

# Carica le variabili dal file .env
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
    market_path = os.path.join(base_dir, "..", "data", "market.json")
    
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
        titolo += "--------------------------------------------------\n\n"

        messaggio = titolo
        for etf in etfs:
            nome = etf.get("label", etf["symbol"])
            variazione_str = etf.get("v_bot", "N/A")
            prezzo = etf.get("price", 0.0)
            
            # --- LOGICA COLORI ---
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
                    icona = "🔵" # AZZURRO per N/A o Errori
            
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


# src//check_alert.py
----------------------------------------
import os
import json
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from utils.logger import log_info, log_error
from dotenv import load_dotenv

load_dotenv()

def get_config():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    conf_path = os.path.join(base_dir, "..", "config", "variations.conf")
    conf = {}
    with open(conf_path, "r") as f:
        for line in f:
            if "=" in line:
                name, value = line.split("=", 1)
                conf[name.strip()] = value.split("#")[0].strip()
    return conf

def check_alert():
    try:
        now = datetime.now(ZoneInfo("Europe/Rome"))
        if now.weekday() > 4: return "weekend"
        if not (now.hour == 19 and 10 <= now.minute <= 20): return "wrong_time"

        conf = get_config()
        
        urls = [
            os.getenv("URL_ALERT_0"),
            os.getenv("URL_ALERT_1"),
            os.getenv("URL_ALERT_2"),
            os.getenv("URL_ALERT_3"),
            os.getenv("URL_ALERT_4"),
            os.getenv("URL_ALERT_5"),
            os.getenv("URL_ALERT_6")
        ]

        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "market.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        etfs = data.get("values", {}).get("data", [])
        best_idx = -1

        for etf in etfs:
            v = etf.get("v_alert", "N/A")
            if v == "N/A": continue
            
            val_str = v.replace("%", "").replace("+", "").strip()
            if val_str and val_str[-1].isalpha(): val_str = val_str[:-1]
            val = float(val_str)

            if val <= float(conf["s_alert_6"]):   idx = 6
            elif val <= float(conf["s_alert_5"]): idx = 5
            elif val <= float(conf["s_alert_4"]): idx = 4
            elif val <= float(conf["s_alert_3"]): idx = 3
            elif val <= float(conf["s_alert_2"]): idx = 2
            elif val <= float(conf["s_alert_1"]): idx = 1
            elif val <= float(conf["s_alert_0"]): idx = 0
            else: idx = -1

            if idx > best_idx: best_idx = idx

        if best_idx != -1:
            requests.get(urls[best_idx], timeout=10)
            log_info(f"ALERTER: Attivato Switch_{best_idx}")
            return "triggered"

        return "no_alert"

    except Exception as e:
        log_error(f"Errore: {e}")
        return "error"

# src//config.py
----------------------------------------
import pendulum
from datetime import datetime
from zoneinfo import ZoneInfo
from utils.logger import log_info, log_error

# Orari mercato LS-TC
MARKET_HOURS = {
    "timezone": "Europe/Rome",
    "open": "07:10",
    "close": "22:55"
}

# Festività italiane fisse
FIXED_HOLIDAYS = [
    (1, 1),   # Capodanno
    (4, 25),  # Liberazione
    (5, 1),   # Lavoro
    (6, 2),   # Repubblica
    (8, 15),  # Ferragosto
    (12, 25), # Natale
    (12, 26), # Santo Stefano
]

# Festività mobili (cache interna)
_cached_easter = {}

def easter_date(year):
    """Calcolo data di Pasqua (algoritmo di Meeus) con cache interna."""
    if year in _cached_easter:
        return _cached_easter[year]

    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19*a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2*e + 2*i - h - k) % 7
    m = (a + 11*h + 22*l) // 451
    month = (h + l - 7*m + 114) // 31
    day = ((h + l - 7*m + 114) % 31) + 1

    pasqua = pendulum.date(year, month, day)
    _cached_easter[year] = pasqua
    return pasqua


def is_market_open(now=None):
    """
    Determina se il mercato è aperto.
    Ora corretta: SEMPRE quella reale del sistema (Europe/Rome),
    convertita in oggetto Pendulum senza conversioni errate.
    """

    # FIX: usa l’ora reale del sistema, non pendulum.now("Europe/Rome")
    if now is None:
        now = pendulum.instance(datetime.now(ZoneInfo("Europe/Rome")))
    else:
        now = pendulum.instance(now).in_timezone("Europe/Rome")

    # DEBUG LOG COMPLETI
    log_info(f"[DEBUG] datetime.now() = {datetime.now()}")
    log_info(f"[DEBUG] datetime.now(ZoneInfo('Europe/Rome')) = {datetime.now(ZoneInfo('Europe/Rome'))}")
    log_info(f"[DEBUG] pendulum.now() = {pendulum.now()}")
    log_info(f"[DEBUG] pendulum.now('Europe/Rome') = {pendulum.now('Europe/Rome')}")
    log_info(f"[DEBUG] now (final) = {now}  tz={now.timezone_name}")

    # Weekend (Pendulum: Monday=1 ... Sunday=7)
    if now.day_of_week in [6, 7]:  # Sabato=6, Domenica=7
        return False

    # Festività fisse
    if (now.month, now.day) in FIXED_HOLIDAYS:
        return False

    # Festività mobili
    year = now.year
    pasqua = easter_date(year)
    pasquetta = pasqua.add(days=1)
    venerdi_santo = pasqua.subtract(days=2)

    if now.date() in [pasqua, pasquetta, venerdi_santo]:
        return False

    # 24 dicembre (vigilia)
    if now.month == 12 and now.day == 24:
        return False

    # 31 dicembre (ultimo dell’anno)
    if now.month == 12 and now.day == 31:
        return False

    # Orari di apertura/chiusura
    open_hour, open_minute = map(int, MARKET_HOURS["open"].split(":"))
    close_hour, close_minute = map(int, MARKET_HOURS["close"].split(":"))

    open_time = now.replace(hour=open_hour, minute=open_minute, second=0)
    close_time = now.replace(hour=close_hour, minute=close_minute, second=0)

    # DEBUG LOG ORARI
    log_info(f"[DEBUG] open_time = {open_time}")
    log_info(f"[DEBUG] close_time = {close_time}")

    return open_time <= now <= close_time


# src//__init__.py
----------------------------------------


# src//report_annuale.py
----------------------------------------
import os
import json
from datetime import datetime
import telebot
from zoneinfo import ZoneInfo
from src.supabase_client import get_supabase
from utils.logger import log_info, log_error
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = telebot.TeleBot(TOKEN)

def genera_grafico_e_report(is_test=False):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    market_path = os.path.join(base_dir, "..", "data", "market.json")

    if not os.path.exists(market_path):
        log_error("Report Annuale: market.json locale non trovato.")
        return

    try:
        with open(market_path, "r", encoding="utf-8") as f:
            market_data = json.load(f)
        etfs = market_data.get("values", {}).get("data", [])
        if not etfs: return

        anno_corrente = datetime.now(ZoneInfo("Europe/Rome")).year
        
        if is_test:
            anno_target = anno_corrente
            data_inizio_query = f"{anno_corrente}-01-01"
            data_fine_query = f"{anno_corrente}-12-31"
            titolo_report = f"🏆 *REPORT PARZIALE {anno_target}*\n"
        else:
            anno_target = anno_corrente - 1
            data_inizio_query = f"{anno_target}-01-01"
            data_fine_query = f"{anno_target}-12-31"
            titolo_report = f"🏆 *REPORT ANNO {anno_target}*\n"
        
        testo_report = titolo_report
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
            log_info(f"Report per l'anno {anno_target} inviato su Telegram.")
        else:
            log_error("Report Annuale: Nessun dato trovato con i filtri impostati.")

    except Exception as e:
        log_error(f"Errore generazione report annuale: {e}")

if __name__ == "__main__":
    genera_grafico_e_report(is_test=True)


# src//scraper_etf.py
----------------------------------------
import os
import json
import base64
import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo

from src import check_alert
from src import backup_manager
from src import bot_telegram
from src import report_annuale
from src.supabase_client import get_supabase, upsert_previous_close
from src.config import is_market_open

from utils.logger import log_info, log_error

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "data"))
CONFIG_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "config"))
etfs_path = os.path.join(DATA_DIR, "etfs.json")
market_path = os.path.join(DATA_DIR, "market.json")
variations_path = os.path.join(CONFIG_DIR, "variations.conf")

# ---------------------------------------------------------
# PERIODI MULTI-VARIAZIONE
# ---------------------------------------------------------
PERIODS = {
    "D":  (1,      "D"),
    "W":  (7,      "W"),
    "M":  (30,     "M"),
    "Q":  (90,     "Q"),
    "H":  (180,    "H"),
    "Y":  (365,    "Y"),
    "3":  (365*3,  "3Y"),
    "5":  (365*5,  "5Y"),
}

# ---------------------------------------------------------
# CARICAMENTO ETF
# ---------------------------------------------------------
def load_etfs():
    try:
        with open(etfs_path, "r", encoding="utf-8") as f:
            etfs = json.load(f)
        log_info(f"Caricati {len(etfs)} ETF da data/etfs.json")
        return etfs
    except Exception as e:
        log_error(f"Errore lettura etfs.json: {e}")
        return []

# ---------------------------------------------------------
# CONFIGURAZIONE VARIAZIONI
# ---------------------------------------------------------
def load_variation_config():
    config = {}
    try:
        if not os.path.exists(variations_path):
            log_error(f"File variazioni non trovato: {variations_path}")
            return {"v1": "D", "v2": "W", "v3": "M", "v_led": "M", "v_alert": "M", "v_bot": "M"}

        with open(variations_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.split("#", 1)[0].strip()
                    config[key] = value

        log_info(f"Configurazione variazioni caricata: {config}")
    except Exception as e:
        log_error(f"Errore lettura variations.conf: {e}")

    return config

# ---------------------------------------------------------
# SCRAPING PREZZO
# ---------------------------------------------------------
def scrape_price(item_id):
    url = f"https://www.ls-tc.de/de/etf/{item_id}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        mid = soup.find("span", attrs={"field": "mid", "item": f"{item_id}@1"})
        if mid and mid.text.strip():
            return float(mid.text.strip().replace(",", "."))
        log_error(f"Prezzo non trovato per item_id {item_id}")
    except Exception as e:
        log_error(f"Errore scraping {item_id}: {e}")
    return None

# ---------------------------------------------------------
# PREVIOUS CLOSE & VARIAZIONI
# ---------------------------------------------------------
def get_previous_close(symbol, supabase):
    today = date.today().isoformat()
    try:
        resp = (
            supabase.table("previous_close")
            .select("close_value")
            .eq("symbol", symbol)
            .filter("snapshot_date", "lt", today)
            .order("snapshot_date", desc=True)
            .limit(1)
            .execute()
        )
        if resp.data:
            return resp.data[0]["close_value"]
    except Exception as e:
        log_error(f"Errore query previous_close {symbol}: {e}")
    return None

def get_price_on_or_before(symbol, target_date, supabase):
    try:
        target_str = target_date.isoformat()
        resp = (
            supabase.table("previous_close")
            .select("close_value")
            .eq("symbol", symbol)
            .filter("snapshot_date", "lte", target_str)
            .order("snapshot_date", desc=True)
            .limit(1)
            .execute()
        )
        if resp.data:
            return float(resp.data[0]["close_value"])
    except Exception as e:
        log_error(f"Errore get_price_on_or_before({symbol}, {target_date}): {e}")
    return None

def calc_variation(price_today, price_past):
    if price_today is None or price_past is None or price_past == 0:
        return None
    return ((price_today - price_past) / price_past) * 100.0

def fmt_variation(value, suffix):
    if value is None:
        return "N/A"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}%{suffix}"

def compute_all_variations(symbol, price_today, today_date, supabase):
    results = {}
    for code, (days, suffix) in PERIODS.items():
        target_date = today_date - timedelta(days=days)
        past_price = get_price_on_or_before(symbol, target_date, supabase)
        variation = calc_variation(price_today, past_price)
        results[code] = fmt_variation(variation, suffix)
    return results

# ---------------------------------------------------------
# SALVATAGGIO market.json
# ---------------------------------------------------------
def save_market_json(results, market_open):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)

        now = datetime.now(ZoneInfo("Europe/Rome"))
        readable = now.strftime("%H:%M %d-%m-%Y")

        data_array = []
        for symbol, etf in results.items():
            if etf.get("status") == "unavailable":
                continue

            daily_change_str = (
                f"{etf['daily_change']:+.2f}" if etf.get("daily_change") is not None else "-"
            )

            entry = {
                "symbol": etf["symbol"],
                "label": etf["label"],
                "price": round(etf["price"], 4),
                "dailyChange": daily_change_str,
                "value": round(etf["price"], 4),
            }

            for key in ("v1", "v2", "v3", "v_led", "v_alert", "v_bot"):
                if key in etf:
                    entry[key] = etf[key]

            data_array.append(entry)

        json_output = {
            "status": "APERTO" if market_open else "CHIUSO",
            "open": market_open,
            "values": {"source": "ls-tc.de", "data": data_array},
            "last_updated": {
                "iso": now.isoformat(),
                "readable": readable
            }
        }

        with open(market_path, "w", encoding="utf-8") as f:
            json.dump(json_output, f, indent=2, ensure_ascii=False)

        log_info(f"market.json salvato con {len(data_array)} ETF")

    except Exception as e:
        log_error(f"Errore salvataggio market.json: {e}")

# ---------------------------------------------------------
# COMMIT GITHUB
# ---------------------------------------------------------
def commit_to_github():
    try:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            log_error("GITHUB_TOKEN non impostato – commit GitHub saltato")
            return

        repo = "Marchino1978/portfolio"
        repo_path = "data/market.json"
        api_url = f"https://api.github.com/repos/{repo}/contents/{repo_path}"

        with open(market_path, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf-8")

        sha = None
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        }
        get_resp = requests.get(api_url, headers=headers, timeout=10)
        if get_resp.status_code == 200:
            sha = get_resp.json().get("sha")

        payload = {
#           "message": "fix",
            "message": "fix\n\n\n[skip ci]",
            "content": content,
            "branch": "main"
        }
        if sha:
            payload["sha"] = sha

        put_resp = requests.put(api_url, headers=headers, json=payload, timeout=10)
        if put_resp.status_code in (200, 201):
            log_info("Commit market.json su GitHub completato")
        else:
            log_error(f"Errore commit GitHub: {put_resp.status_code} – {put_resp.text}")

    except Exception as e:
        log_error(f"Errore durante commit GitHub: {e}")

# ---------------------------------------------------------
# FUNZIONE PRINCIPALE
# ---------------------------------------------------------
def main():
    log_info("=== INIZIO aggiornamento ETF ===")
    today_date = date.today()
    today_str = today_date.isoformat()
    market_open = is_market_open()

    supabase = get_supabase()
    ETFS = load_etfs()
    if not ETFS:
        log_error("Nessun ETF caricato – aggiornamento interrotto")
        return {}, market_open

    variation_config = load_variation_config()

    results = {}

    for etf in ETFS:
        symbol = etf["symbol"]
        label = etf["label"]
        item_id = etf["item_id"]

        log_info(f"Scraping {symbol} ({label}) – item_id {item_id}")
        price = scrape_price(item_id)

        if price is None:
            results[symbol] = {"status": "unavailable", "symbol": symbol, "label": label}
            continue

        prev = get_previous_close(symbol, supabase)
        daily_change = calc_variation(price, prev) if prev else None

        if market_open:
            upsert_previous_close(
                symbol=symbol,
                label=label,
                close_value=price,
                snapshot_date=today_str,
                daily_change=daily_change
            )

        all_variations = compute_all_variations(symbol, price, today_date, supabase)

        results[symbol] = {
            "symbol": symbol,
            "label": label,
            "price": price,
            "previous_close": prev,
            "daily_change": daily_change,
            "snapshot_date": today_str,
            "status": "open" if market_open else "closed",
            "v1": all_variations.get(variation_config.get("v1", "D"), "N/A"),
            "v2": all_variations.get(variation_config.get("v2", "W"), "N/A"),
            "v3": all_variations.get(variation_config.get("v3", "M"), "N/A"),
            "v_led": all_variations.get(variation_config.get("v_led", "M"), "N/A"),
            "v_alert": all_variations.get(variation_config.get("v_alert", "M"), "N/A"),
            "v_bot": all_variations.get(variation_config.get("v_bot", "M"), "N/A"),
        }

    save_market_json(results, market_open)
    commit_to_github()

    # ---------------------------------------------------------
    # ALERT su AMAZON ALEXA
    # ---------------------------------------------------------
    try:
        check_alert.check_alert()
        log_info("Controllo alert Alexa eseguito.")
    except Exception as e:
        log_error(f"Errore controllo alert Alexa: {e}")

    # ---------------------------------------------------------
    # BACKUP SUPABASE (settimanale) + REPORT TELEGRAM (mensile/annuale)
    # ---------------------------------------------------------
    now_rome = datetime.now(ZoneInfo("Europe/Rome"))
    giorno_settimana = now_rome.weekday() # 0=Lunedì, 6=Domenica

    # 1. BACKUP SUPABASE (settimanale)
    if giorno_settimana == 0 and 5 <= now_rome.minute <= 25 and now_rome.hour == 7:
        log_info(f"Avvio backup settimanale ({now_rome.day}/{now_rome.month})...")
        try:
            path_sql = backup_manager.run_supabase_backup()
            if path_sql:
                # Se il backup è riuscito, caricalo su GitHub (gestisce la rotazione a 3 file)
                backup_manager.upload_backup_to_github(path_sql)
        except Exception as e:
            log_error(f"Errore esecuzione backup/upload settimanale: {e}")

    # 2. REPORT TELEGRAM (mensile)
    invia_oggi = False

    # CASO 1: Oggi è il 1° del mese ed è un giorno lavorativo (Lun-Ven)
    if now_rome.day == 1 and giorno_settimana < 5:
        invia_oggi = True

    # CASO 2: Il 1° era Sabato o Domenica e oggi è Lunedì (2 o 3 del mese)
    elif giorno_settimana == 0 and (now_rome.day == 2 or now_rome.day == 3):
        invia_oggi = True

    # Esegui l'invio solo nella finestra oraria del primo cron (07:03 - 07:23)
    if invia_oggi and 3 <= now_rome.minute <= 23 and now_rome.hour == 7:
        log_info(f"Condizione report mensile soddisfatta ({now_rome.day}/{now_rome.month}). Invio...")
        try:
            # import bot_telegram
            bot_telegram.send_monthly_report()
            log_info("Report Telegram inviato con successo.")
        except Exception as e:
            log_error(f"Errore invio Telegram: {e}")

    # 3. REPORT ANNUALE TELEGRAM CON GRAFICO
    invia_annuale = False

    # Verifica se è gennaio, se è lunedì (0) e se il giorno cade nella prima settimana (1-7)
    if now_rome.month == 1 and giorno_settimana == 0 and 1 <= now_rome.day <= 7:
        invia_annuale = True

    # Esegui l'invio solo nella finestra oraria del primo cron (07:03 - 07:23)
    if invia_annuale and 3 <= now_rome.minute <= 23 and now_rome.hour == 7:
        log_info(f"Condizione report annuale soddisfatta ({now_rome.day}/{now_rome.month}). Generazione grafico...")
        try:
            # import report_anuale
            report_annuale.genera_grafico_e_report()
            log_info("Report annuale e grafico inviati con successo su Telegram.")
        except Exception as e:
            log_error(f"Errore invio report annuale con grafico: {e}")


    log_info(f"=== FINE aggiornamento ETF – {len([r for r in results.values() if r.get('status') != 'unavailable'])} ETF aggiornati ===")
    return results, market_open

if __name__ == "__main__":
    main()

# src//scraper_fondi.py
----------------------------------------
import csv
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import os
from io import StringIO
import base64

from utils.logger import log_info, log_error

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "data"))
fondi_path = os.path.join(DATA_DIR, "fondi.csv")
fondi_nav_path = os.path.join(DATA_DIR, "fondi_nav.csv")

# -----------------------------
# Fetch & Parser
# -----------------------------
def fetch_html(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.text
    except Exception as e:
        log_error(f"Errore fetch {url}: {e}")
        return None

def parse_eurizon(html):
    soup = BeautifulSoup(html, "html.parser")
    span = soup.find("span", class_="product-dashboard-token-value-bold")
    if span and span.get_text(strip=True):
        return span.get_text(strip=True)
    match = re.search(r"\d{1,3}(\.\d{3})*,\d{2}", soup.get_text())
    return match.group(0) if match else None

def parse_teleborsa(html):
    soup = BeautifulSoup(html, "html.parser")
    price_span = soup.find("span", id="ctl00_phContents_ctlHeader_lblPrice")
    if price_span and price_span.get_text(strip=True):
        return price_span.get_text(strip=True)
    alt = soup.find("span", id=re.compile(r"lblPrice", re.I))
    if alt and alt.get_text(strip=True):
        return alt.get_text(strip=True)
    match = re.search(r"\d{1,3}(\.\d{3})*,\d{2}", soup.get_text())
    return match.group(0) if match else None

def normalize(value_it):
    if not value_it:
        return None
    s = value_it.strip().replace(".", "").replace(",", ".")
    return s

# -----------------------------
# Commit GitHub
# -----------------------------
def commit_to_github():
    try:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            log_error("GITHUB_TOKEN non impostato – commit GitHub saltato")
            return

        repo = "Marchino1978/portfolio"
        repo_path = "data/fondi_nav.csv"
        api_url = f"https://api.github.com/repos/{repo}/contents/{repo_path}"

        with open(fondi_nav_path, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf-8")

        sha = None
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        }
        get_resp = requests.get(api_url, headers=headers, timeout=10)
        if get_resp.status_code == 200:
            sha = get_resp.json().get("sha")

        payload = {
#           "message": "fix",
            "message": "fix\n\n\n[skip ci]",
            "content": content,
            "branch": "main"
        }
        if sha:
            payload["sha"] = sha

        put_resp = requests.put(api_url, headers=headers, json=payload, timeout=10)
        if put_resp.status_code in (200, 201):
            log_info("Commit fondi_nav.csv su GitHub completato")
        else:
            log_error(f"Errore commit GitHub: {put_resp.status_code} – {put_resp.text}")

    except Exception as e:
        log_error(f"Errore durante commit GitHub: {e}")

# -----------------------------
# Main
# -----------------------------
def main():
    log_info("=== INIZIO aggiornamento fondi ===")
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(fondi_path):
        log_error(f"File fondi.csv non trovato: {fondi_path}")
        return

    with open(fondi_path, newline="", encoding="utf-8") as f:
        lines = [line for line in f if line.strip() and not line.strip().startswith("#")]

    clean_csv = StringIO("".join(lines))
    reader = csv.DictReader(clean_csv)
    reader.fieldnames = [fn.strip().lstrip("\ufeff") for fn in reader.fieldnames]

    fondi = [row for row in reader if any(row.values())]

    with open(fondi_nav_path, "w", newline="", encoding="utf-8") as f_out:
        writer = csv.writer(f_out, delimiter=";")
        writer.writerow(["timestamp", "nome", "ISIN", "nav_text_it", "nav_float"])

        for fondo in fondi:
            nome = fondo.get("nome", "").strip()
            url = fondo.get("url", "").strip()
            isin = fondo.get("ISIN", "").strip()

            if not url:
                writer.writerow([datetime.now().isoformat(), nome, isin, "NO_URL", ""])
                log_error(f"{nome} ({isin}): URL mancante")
                continue

            html = fetch_html(url)
            if "eurizoncapital.com" in url:
                nav_text = parse_eurizon(html) if html else None
            elif "teleborsa.it" in url:
                nav_text = parse_teleborsa(html) if html else None
            else:
                nav_text = None

            nav_float = normalize(nav_text)

            writer.writerow([
                datetime.now().isoformat(),
                nome,
                isin,
                nav_text or "N/D",
                nav_float or "N/D"
            ])
            status = nav_text or "N/D"
            log_info(f"{nome} ({isin}): {status}")

    commit_to_github()
    log_info("=== FINE aggiornamento fondi ===")

if __name__ == "__main__":
    main()

# src//supabase_client.py
----------------------------------------
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# ---------------------------------------------------------
# FACTORY
# ---------------------------------------------------------
def get_supabase() -> Client:
    load_dotenv()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")
    return create_client(url, key)

# ---------------------------------------------------------
# UPSERT PREVIOUS CLOSE
# ---------------------------------------------------------
def upsert_previous_close(symbol, label, close_value, snapshot_date, daily_change=None):
    supabase = get_supabase() 

    data = {
        "symbol": symbol,
        "label": label,
        "close_value": round(close_value, 2),
        "snapshot_date": snapshot_date,
        "daily_change": round(daily_change, 2) if daily_change is not None else None
    }

    # 1. Controllo se esiste già una riga per symbol + snapshot_date
    existing = (
        supabase.table("previous_close")
        .select("*")
        .eq("symbol", symbol)
        .eq("snapshot_date", snapshot_date)
        .execute()
    )

    # 2. Se esiste → UPDATE
    if existing.data:
        supabase.table("previous_close") \
            .update(data) \
            .eq("symbol", symbol) \
            .eq("snapshot_date", snapshot_date) \
            .execute()
    else:
        # 3. Se non esiste → INSERT
        supabase.table("previous_close") \
            .insert(data) \
            .execute()


