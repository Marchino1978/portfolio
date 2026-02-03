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