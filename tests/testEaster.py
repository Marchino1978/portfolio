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
#