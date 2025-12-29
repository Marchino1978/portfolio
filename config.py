import pendulum

# Orari mercato LS-TC
MARKET_HOURS = {
    "timezone": "Europe/Rome",
    "open": "07:20",
    "close": "23:00"
}

# Festività italiane fisse
FIXED_HOLIDAYS = [
    (1, 1), (4, 25), (5, 1), (6, 2), (8, 15), (12, 25), (12, 26)
]

def is_market_open(now=None):
    # Se non viene passato un datetime, usa quello attuale
    if now is None:
        now = pendulum.now(MARKET_HOURS["timezone"])
    else:
        now = now.in_timezone(MARKET_HOURS["timezone"])

    # Weekend (Pendulum: Monday=1 ... Sunday=7)
    if now.day_of_week in [6, 7]:  # Sabato=6, Domenica=7
        return False

    # Festività fisse
    if (now.month, now.day) in FIXED_HOLIDAYS:
        return False

    # TODO: Pasqua e Pasquetta (come nel tuo config.js)

    # Orari di apertura/chiusura
    open_hour, open_minute = map(int, MARKET_HOURS["open"].split(":"))
    close_hour, close_minute = map(int, MARKET_HOURS["close"].split(":"))

    open_time = now.replace(hour=open_hour, minute=open_minute, second=0)
    close_time = now.replace(hour=close_hour, minute=close_minute, second=0)

    return open_time <= now <= close_time
