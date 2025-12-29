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