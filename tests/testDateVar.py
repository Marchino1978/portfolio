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
