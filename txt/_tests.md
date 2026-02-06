# tests//testDateVar.py
----------------------------------------
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from utils.holidays import easter_date, is_holiday

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
from datetime import date
from utils.holidays import easter_date

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

