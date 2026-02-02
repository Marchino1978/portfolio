import os
import base64
import requests
from datetime import datetime
from supabase_client import get_supabase
from utils.logger import log_info, log_error

def run_supabase_backup():
    """Estrae i dati da Supabase e salva un file .sql in /data."""
    table_name = "previous_close"
    filename = f"backup_supabase_{datetime.now().strftime('%Y_%m')}.sql"
    file_path = os.path.join("data", filename)
    
    log_info(f"Inizio generazione backup SQL: {filename}")
    
    try:
        supabase = get_supabase()
        resp = supabase.table(table_name).select("*").order("snapshot_date", desc=True).execute()
        rows = resp.data

        if not rows:
            log_error("Backup fallito: nessun dato trovato nella tabella.")
            return None # Restituiamo None per indicare fallimento

        os.makedirs("data", exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"-- BACKUP AUTOMATICO: {table_name}\n")
            f.write(f"-- DATA: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"TRUNCATE TABLE {table_name};\n\n")

            for row in rows:
                cols = ", ".join(row.keys())
                vals = []
                for v in row.values():
                    if v is None: vals.append("NULL")
                    elif isinstance(v, (int, float)): vals.append(str(v))
                    else:
                        clean_v = str(v).replace("'", "''")
                        vals.append(f"'{clean_v}'")
                f.write(f"INSERT INTO {table_name} ({cols}) VALUES ({', '.join(vals)});\n")
        
        log_info(f"Backup locale completato: {file_path}")
        return file_path # Restituiamo il percorso del file creato
        
    except Exception as e:
        log_error(f"Errore critico durante il backup SQL: {e}")
        return None

def upload_backup_to_github(file_path):
    """Carica il file SQL su GitHub via API."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log_error("GITHUB_TOKEN mancante, upload backup saltato.")
        return False

    repo = "Marchino1978/portfolio"
    file_name = os.path.basename(file_path)
    # Il percorso nel repo sarà data/nome_file.sql
    api_url = f"https://api.github.com/repos/{repo}/contents/data/{file_name}"

    try:
        with open(file_path, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf-8")

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        }

        # Controlliamo se esiste già (opzionale per i backup mensili)
        get_resp = requests.get(api_url, headers=headers, timeout=10)
        sha = get_resp.json().get("sha") if get_resp.status_code == 200 else None

        payload = {
            "message": f"Backup mensile database {file_name} [auto]",
            "content": content,
            "branch": "main"
        }
        if sha: payload["sha"] = sha

        put_resp = requests.put(api_url, headers=headers, json=payload, timeout=10)
        if put_resp.status_code in (200, 201):
            log_info(f"File {file_name} caricato con successo su GitHub.")
            return True
        else:
            log_error(f"Errore upload GitHub: {put_resp.text}")
            return False
    except Exception as e:
        log_error(f"Errore durante l'upload del backup: {e}")
        return False

if __name__ == "__main__":
    path = run_supabase_backup()
    if path:
        upload_backup_to_github(path)