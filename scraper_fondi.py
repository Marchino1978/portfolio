import csv
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import os
from io import StringIO
import base64

from utils.logger import log_info, log_error

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
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
def commit_csv_to_github(path, message):
    try:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            log_info("GITHUB_TOKEN non impostato – commit saltato")
            return

        repo = "Marchino1978/portfolio"
        api_url = f"https://api.github.com/repos/{repo}/contents/{path}"

        with open(path, "rb") as f:
            content = base64.b64encode(f.read()).decode()

        sha = None
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
        resp = requests.get(api_url, headers=headers, timeout=10)
        if resp.status_code == 200:
            sha = resp.json().get("sha")

        payload = {"message": message, "content": content, "branch": "main"}
        if sha:
            payload["sha"] = sha

        put_resp = requests.put(api_url, headers=headers, json=payload, timeout=10)
        if put_resp.status_code in (200, 201):
            log_info(f"Commit GitHub OK: {path}")
        else:
            log_error(f"Errore commit GitHub: {put_resp.status_code} – {put_resp.text}")
    except Exception as e:
        log_error(f"Errore commit fondi_nav.csv: {e}")

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

    commit_csv_to_github("data/fondi_nav.csv", "fix")
    log_info("=== FINE aggiornamento fondi ===")