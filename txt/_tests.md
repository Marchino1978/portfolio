# tests//testDateVar.py
----------------------------------------
import sys
import os
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import utils.holidays as holidays_mod
holidays_mod.timedelta = timedelta

from utils.holidays import easter_date, is_holiday

def is_weekend(d):
    return d.weekday() >= 5  # sabato = 5, domenica = 6

def previous_business_day(target_date):
    holidays_set = set()
    year = target_date.year
    # Festività fisse
    fixed = [(1,1), (4,25), (5,1), (6,2), (8,15), (12,25), (12,26)]
    for m, d_f in fixed:
        holidays_set.add(date(year, m, d_f))
    # Pasqua e Pasquetta
    easter = easter_date(year)
    holidays_set.add(easter)
    holidays_set.add(easter + timedelta(days=1))

    d = target_date
    while is_weekend(d) or d in holidays_set:
        d -= timedelta(days=1)
    return d

def get_target_date(today, months_back=1):
    target = today - relativedelta(months=months_back)
    day = today.day
    
    last_day_month = date(target.year, target.month, 1) + relativedelta(months=1) - timedelta(days=1)
    
    if day > last_day_month.day:
        day = last_day_month.day
    candidate = date(target.year, target.month, day)

    if is_weekend(candidate) or is_holiday(candidate):
        return previous_business_day(candidate)
    return candidate

if __name__ == "__main__":
    # Esempi di test
    today = date(2025, 4, 22)

    print("--- Risultati Automatici ---")
    print("Target  1 mese fa:", get_target_date(today, 1))
    print("Target  3 mesi fa:", get_target_date(today, 3))
    print("Target  6 mesi fa:", get_target_date(today, 6))
    print("Target  9 mesi fa:", get_target_date(today, 9))
    print("Target 12 mesi fa:", get_target_date(today, 12))


# tests//testEaster.py
----------------------------------------
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

