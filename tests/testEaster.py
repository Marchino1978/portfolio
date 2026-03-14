import sys
import os
from datetime import date, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from utils.holidays import easter_date
except ImportError:
    print("❌ Errore: Assicurati che utils/holidays.py esista e contenga easter_date.")
    sys.exit(1)

def test_easter_year(year, expected_date_str):
    expected = date.fromisoformat(expected_date_str)
    result = easter_date(year)
    if result == expected:
        print(f"✅ Pasqua {year}: OK ({result})")
    else:
        print(f"❌ Pasqua {year}: attesa {expected_date_str}, ottenuta {result}")

def test_pasquetta_year(year, expected_date_str):
    easter = easter_date(year)
    pasquetta = easter + timedelta(days=1)
    expected = date.fromisoformat(expected_date_str)
    if pasquetta == expected:
        print(f"✅ Pasquetta {year}: OK ({pasquetta})")
    else:
        print(f"❌ Pasquetta {year}: attesa {expected_date_str}, ottenuta {pasquetta}")

if __name__ == "__main__":
    print(f"--- Inizio Test Pasqua/Pasquetta ---\n")
    
    # Test su anni noti
    anni_test = [
        (2020, "2020-04-12", "2020-04-13"),
        (2021, "2021-04-04", "2021-04-05"),
        (2022, "2022-04-17", "2022-04-18"),
        (2023, "2023-04-09", "2023-04-10"),
        (2024, "2024-03-31", "2024-04-01"),
        (2025, "2025-04-20", "2025-04-21"),
        (2026, "2026-04-05", "2026-04-06"),
        (2027, "2027-03-28", "2027-03-29"),
        (2028, "2028-04-16", "2028-04-17"),
        (2029, "2029-04-01", "2029-04-02"),
    ]

    for anno, p_data, pq_data in anni_test:
        test_easter_year(anno, p_data)
        test_pasquetta_year(anno, pq_data)

    print("\n--- Test completati. ---")

    # Test manuale interattivo
    print("\n--- Test Manuale ---")
    try:
        year_input = int(input("Inserisci anno per test Pasqua/Pasquetta: "))
        easter = easter_date(year_input)
        pasquetta = easter + timedelta(days=1)
        print(f"Pasqua {year_input}: {easter}")
        print(f"Pasquetta {year_input}: {pasquetta}")
    except ValueError:
        print("Anno non valido.")