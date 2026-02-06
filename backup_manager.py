import os
import base64
import requests
from datetime import datetime
from supabase_client import get_supabase
from utils.logger import log_info, log_error

def run_supabase_backup():
    table_name = "previous_close"
    folder = "backup_SQL"
    filename = f"backup_supabase_{datetime.now().strftime('%Y_%m_%d')}.sql"
    file_path = os.path.join(folder, filename)
    
    log_info(f"Inizio generazione backup SQL: {filename}")
    
    try:
        supabase = get_supabase()
        resp = supabase.table(table_name).select("*").order("snapshot_date", desc=True).execute()
        rows = resp.data
        if not rows: return None
        
        os.makedirs(folder, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"-- BACKUP AUTOMATICO: {table_name}\n\n")
            f.write(f"TRUNCATE TABLE {table_name};\n\n")
            for row in rows:
                cols = ", ".join(row.keys())
                vals = [f"'{str(v).replace("'", "''")}'" if v is not None and not isinstance(v, (int, float)) else str(v) if v is not None else "NULL" for v in row.values()]
                f.write(f"INSERT INTO {table_name} ({cols}) VALUES ({', '.join(vals)});\n")
        
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

        resp = requests.get(api_url_base, headers=headers, timeout=10)
        if resp.status_code == 200:
            files = resp.json()
            backups = sorted([f for f in files if f['name'].endswith(".sql")], 
                            key=lambda x: x['name'], reverse=True)

            if len(backups) > 3:
                for old_file in backups[3:]:
                    del_url = f"https://api.github.com/repos/{repo}/contents/{old_file['path']}"
                    requests.delete(del_url, headers=headers, json={
                        "message": f"Rotazione backup: rimosso {old_file['name']}",
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