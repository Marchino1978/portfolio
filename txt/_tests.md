# tests//testDateVar.py
----------------------------------------
# tests/testDateVar.py
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from utils.holidays import easter_date, is_holiday  # assumiamo funzioni in utils/holidays.py

def is_weekend(d):
    return d.weekday() >= 5  # sabato = 5, domenica = 6

def previous_business_day(target_date):
    holidays = set()
    year = target_date.year
    # Festività fisse
    fixed = [(1,1), (4,25), (5,1), (6,2), (8,15), (12,25), (12,26)]
    for m, d in fixed:
        holidays.add(date(year, m, d))
    # Pasqua e Pasquetta
    easter = easter_date(year)
    holidays.add(easter)
    holidays.add(easter + timedelta(days=1))

    d = target_date
    while is_weekend(d) or d in holidays:
        d -= timedelta(days=1)
    return d

def get_target_date(today, months_back=1):
    target = today - relativedelta(months=months_back)
    day = today.day
    last_day_month = date(target.year, target.month + 1, 1) - timedelta(days=1)
    if day > last_day_month.day:
        day = last_day_month.day
    candidate = date(target.year, target.month, day)

    if is_weekend(candidate) or is_holiday(candidate):
        return previous_business_day(candidate)
    return candidate

if __name__ == "__main__":
    # Esempi di test
    today = date(2025, 12, 29)  # lunedì 29 dicembre 2025

    print("Target 1 mese fa:", get_target_date(today, 1))
    print("Target 3 mesi fa:", get_target_date(today, 3))

    # Test manuale interattivo (opzionale)
    year = int(input("\nInserisci anno per test Pasqua/Pasquetta: "))
    easter = easter_date(year)
    pasquetta = easter + timedelta(days=1)
    print(f"Pasqua {year}: {easter}")
    print(f"Pasquetta {year}: {pasquetta}")

# tests//testEaster.py
----------------------------------------
# tests/testEaster.py
from datetime import date
from utils.holidays import easter_date  # assumiamo che la funzione sia in utils/holidays.py

def test_easter_year(year, expected_date_str):
    expected = date.fromisoformat(expected_date_str)
    result = easter_date(year)
    if result == expected:
        print(f"✅ Pasqua {year}: OK ({result})")
    else:
        print(f"❌ Pasqua {year}: attesa {expected_date_str}, ottenuta {result}")

def test_pasquetta_year(year, expected_date_str):
    easter = easter_date(year)
    pasquetta = date(easter.year, easter.month, easter.day + 1)
    expected = date.fromisoformat(expected_date_str)
    if pasquetta == expected:
        print(f"✅ Pasquetta {year}: OK ({pasquetta})")
    else:
        print(f"❌ Pasquetta {year}: attesa {expected_date_str}, ottenuta {pasquetta}")

if __name__ == "__main__":
    # Test su anni noti
    test_easter_year(2024, "2024-03-31")
    test_easter_year(2025, "2025-04-20")
    test_easter_year(2026, "2026-04-05")
    test_easter_year(2027, "2027-03-28")

    test_pasquetta_year(2024, "2024-04-01")
    test_pasquetta_year(2025, "2025-04-21")
    test_pasquetta_year(2026, "2026-04-06")
    test_pasquetta_year(2027, "2027-03-29")

    print("Test Pasqua/Pasquetta completati.")

# tests//test_etf.py
----------------------------------------
import json
from unittest.mock import patch, MagicMock
from scraper_etf import scrape_price, get_previous_close, update_all_etf

# Carica etfs.json per i test
with open("etfs.json", "r") as f:
    ETFS = json.load(f)

def test_scrape_price_success():
    # Mock risposta HTML con mid = "123,45"
    mock_html = '''
    <span field="mid" item="1045562@1" source="lightstreamer">123,45</span>
    '''
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = mock_html
        mock_get.return_value = mock_resp

        price = scrape_price("1045562")
        assert price == 123.45

def test_scrape_price_no_mid():
    mock_html = '<html><body>No price</body></html>'
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = mock_html
        mock_get.return_value = mock_resp

        price = scrape_price("999999")
        assert price is None

@patch("supabase_client.supabase")
def test_get_previous_close(mock_supabase):
    mock_resp = MagicMock()
    mock_resp.data = [{"close_value": 100.0}]
    mock_table = MagicMock()
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.lt.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.execute.return_value = mock_resp
    mock_supabase.table.return_value = mock_table

    prev = get_previous_close("VUAA")
    assert prev == 100.0

@patch("scraper_etf.scrape_price")
@patch("scraper_etf.get_previous_close")
@patch("scraper_etf.is_market_open", return_value=True)
@patch("scraper_etf.upsert_previous_close")
def test_update_all_etf(mock_upsert, mock_market, mock_prev, mock_scrape):
    mock_scrape.side_effect = [150.0, 200.0]  # prezzi per primi 2 ETF
    mock_prev.side_effect = [100.0, 180.0]   # previous close

    results, market_open = update_all_etf()

    assert market_open is True
    assert len(results) == len(ETFS)
    assert results["VUAA"]["price"] == 150.0
    assert results["VUAA"]["dailyChange"] == 50.0
    assert mock_upsert.called

if __name__ == "__main__":
    import pytest
    pytest.main(["-v"])

# tests//test_fondi.py
----------------------------------------
from scraper_fondi import main as scrape_fondi
from unittest.mock import patch

@patch("requests.get")
def test_scrape_fondi_eurizon(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = '<span class="product-dashboard-token-value-bold color-green">123,45</span>'
    mock_get.return_value = mock_resp

    # Mock open per fondi.csv e fondi_nav.csv
    mock_csv = "nome,url,ISIN\ntest,https://www.eurizoncapital.com/test,LU1234567890\n"
    with patch("builtins.open", side_effect=[MagicMock(__enter__=MagicMock(return_value=mock_csv.splitlines())), MagicMock()]):
        scrape_fondi()
        # Verifica che abbia scritto correttamente
        # (aggiungi assert su output se vuoi)

