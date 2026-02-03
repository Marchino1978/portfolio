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
#