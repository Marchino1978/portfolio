import csv
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import os
from io import StringIO  # <-- Aggiunto per ricostruire il CSV pulito

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# -----------------------------
# Percorsi robusti
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "../data")
fondi_path = os.path.join(DATA_DIR, "fondi.csv")
fondi_nav_path = os.path.join(DATA_DIR, "fondi_nav.csv")

# -----------------------------
# Fetch HTML con gestione errori
# -----------------------------
def fetch_html(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        if not r.text or len(r.text.strip()) == 0:
            raise ValueError("HTML vuoto da " + url)
        return r.text
    except Exception as e:
        print(f"Errore fetch {url}: {e}")
        return None

# -----------------------------
# Parser Eurizon
# -----------------------------
def parse_eurizon(html):
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    span = soup.find("span", class_="product-dashboard-token-value-bold color-green")
    if span and span.get_text(strip=True):
        return span.get_text(strip=True)
    text = soup.get_text(" ", strip=True)
    match = re.search(r"\b\d{1,3}(\.\d{3})*,\d{2}\b|\b\d+,\d{2}\b", text)
    if match:
        return match.group(0)
    return None

# -----------------------------
# Parser Teleborsa
# -----------------------------
def parse_teleborsa(html):
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    price_span = soup.find("span", id="ctl00_phContents_ctlHeader_lblPrice")
    if price_span:
        raw = price_span.get_text(strip=True)
        if raw:
            return raw
    alt = soup.find("span", id=re.compile(r"lblPrice", re.I))
    if alt:
        raw = alt.get_text(strip=True)
        if raw:
            return raw
    text = soup.get_text(" ", strip=True)
    match = re.search(r"\b\d{1,3}(\.\d{3})*,\d{2}\b|\b\d{1,3}(\.\d{3})*\b", text)
    if match:
        return match.group(0)
    return None

# -----------------------------
# Normalizzazione valori IT -> EN
# -----------------------------
def normalize(value_it):
    if not value_it:
        return None
    s = value_it.strip()
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(".", "")
    return s

# -----------------------------
# Main
# -----------------------------
def main():
    # ⚠️ Nessun controllo orario: il cron esterno decide QUANDO eseguire

    # Legge lista fondi da CSV (con supporto per commenti # e righe vuote)
    fondi = []
    with open(fondi_path, newline="", encoding="utf-8") as f:
        lines = f.readlines()

    # Filtra righe vuote e commenti (quelli che iniziano con #)
    clean_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        clean_lines.append(line)

    # Ricostruisci un file-like object pulito per DictReader
    clean_csv = StringIO("".join(clean_lines))

    reader = csv.DictReader(clean_csv)

    # Pulizia fieldnames (rimuove BOM e spazi)
    if reader.fieldnames:
        reader.fieldnames = [fn.strip().lstrip("\ufeff") for fn in reader.fieldnames]

    for row in reader:
        # Pulizia chiavi e valori
        clean_row = {k.strip(): v.strip() for k, v in row.items() if k is not None}
        # Salta righe completamente vuote dopo la pulizia
        if not any(clean_row.values()):
            continue
        fondi.append(clean_row)

    # Scrive output una sola volta (sovrascrive ogni run)
    with open(fondi_nav_path, "w", newline="", encoding="utf-8") as f_out:
        writer = csv.writer(f_out, delimiter=";")
        writer.writerow(["timestamp", "nome", "ISIN", "nav_text_it", "nav_float"])

        # Loop sui fondi
        for fondo in fondi:
            nome = fondo.get("nome", "")
            url = fondo.get("url", "")
            isin = fondo.get("ISIN", "")
            try:
                html = fetch_html(url)
                if not html:
                    raise ValueError("HTML non disponibile")

                if "eurizoncapital.com" in url:
                    nav_text = parse_eurizon(html)
                elif "teleborsa.it" in url:
                    nav_text = parse_teleborsa(html)
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
                print(f"{nome} ({isin}): {nav_text or 'N/D'}")

            except Exception as e:
                writer.writerow([datetime.now().isoformat(), nome, isin, "ERRORE", ""])
                print(f"{nome} ({isin}): errore {repr(e)}")

if __name__ == "__main__":
    main()