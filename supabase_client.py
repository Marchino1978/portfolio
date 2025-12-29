from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)

def upsert_previous_close(symbol, label, close_value, snapshot_date, daily_change=None):
    data = {
        "symbol": symbol,
        "label": label,
        "close_value": round(close_value, 2),
        "snapshot_date": snapshot_date,
        "daily_change": round(daily_change, 2) if daily_change is not None else None
    }

    # 1. Controllo se esiste già una riga per symbol + snapshot_date
    existing = supabase.table("previous_close") \
        .select("*") \
        .eq("symbol", symbol) \
        .eq("snapshot_date", snapshot_date) \
        .execute()

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
