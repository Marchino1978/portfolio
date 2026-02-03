from datetime import datetime

def log_info(msg):
    print(f"[{datetime.now().isoformat()}] INFO {msg}")

def log_error(msg):
    print(f"[{datetime.now().isoformat()}] ERROR {msg}")
//