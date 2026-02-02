import os
from datetime import datetime
from supabase_client import get_supabase
from utils.logger import log_info, log_error

def run_supabase_backup():
    """Estrae i dati da Supabase e salva un file .sql in /data."""
    table_name = "previous_close"
    # Nome file con mese e anno per avere uno storico su GitHub
    filename = f"backup_supabase_{datetime.now().strftime('%Y_%m')}.sql"
    file_path = os.path.join("data", filename)
    
    log_info(f"Inizio generazione backup SQL: {filename}")
    
    try:
        supabase = get_supabase()
        # Recupero dati ordinati
        resp = supabase.table(table_name).select("*").order("snapshot_date", desc=True).execute()
        rows = resp.data

        if not rows:
            log_error("Backup fallito: nessun dato trovato nella tabella.")
            return False

        # Crea la cartella data se non esiste (sicurezza extra)
        os.makedirs("data", exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"-- BACKUP AUTOMATICO: {table_name}\n")
            f.write(f"-- DATA: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"TRUNCATE TABLE {table_name};\n\n")

            for row in data:
                cols = ", ".join(row.keys())
                vals = []
                for v in row.values():
                    if v is None: 
                        vals.append("NULL")
                    elif isinstance(v, (int, float)): 
                        vals.append(str(v))
                    else:
                        # Escape apici singoli per SQL
                        clean_v = str(v).replace("'", "''")
                        vals.append(f"'{clean_v}'")
                
                f.write(f"INSERT INTO {table_name} ({cols}) VALUES ({', '.join(vals)});\n")
        
        log_info(f"Backup completato con successo: {file_path}")
        return True
        
    except Exception as e:
        log_error(f"Errore critico durante il backup SQL: {e}")
        return False

if __name__ == "__main__":
    # Test rapido se lanciato manualmente: python backup_manager.py
    run_supabase_backup()