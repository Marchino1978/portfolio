import pendulum

# Orari mercato LS-TC
MARKET_HOURS = {
    "timezone": "Europe/Rome",
    "open": "07:20",
    "close": "23:00"
}

# Festività italiane fisse
FIXED_HOLIDAYS = [
    (1, 1),   # Capodanno
    (4, 25),  # Liberazione
    (5, 1),   # Lavoro
    (6, 2),   # Repubblica
    (8, 15),  # Ferragosto
    (12, 25), # Natale
    (12, 26), # Santo Stefano
]

# Festività mobili (cache interna)
_cached_easter = {}

def easter_date(year):
    """Calcolo data di Pasqua (algoritmo di Meeus) con cache interna."""
    if year in _cached_easter:
        return _cached_easter[year]

    # Algoritmo di Meeus
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19*a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2*e + 2*i - h - k) % 7
    m = (a + 11*h + 22*l) // 451
    month = (h + l - 7*m + 114) // 31
    day = ((h + l - 7*m + 114) % 31) + 1

    pasqua = pendulum.date(year, month, day)
    _cached_easter[year] = pasqua
    return pasqua

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

    # Festività mobili
    year = now.year
    pasqua = easter_date(year)
    pasquetta = pasqua.add(days=1)
    venerdi_santo = pasqua.subtract(days=2)

    if now.date() in [pasqua, pasquetta, venerdi_santo]:
        return False

    # 24 dicembre (vigilia)
    if now.month == 12 and now.day == 24:
        return False

    # 31 dicembre (ultimo dell’anno)
    if now.month == 12 and now.day == 31:
        return False

    # Orari di apertura/chiusura
    open_hour, open_minute = map(int, MARKET_HOURS["open"].split(":"))
    close_hour, close_minute = map(int, MARKET_HOURS["close"].split(":"))

    open_time = now.replace(hour=open_hour, minute=open_minute, second=0)
    close_time = now.replace(hour=close_hour, minute=close_minute, second=0)

    return open_time <= now <= close_time
