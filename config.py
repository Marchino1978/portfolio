from luxon import DateTime

# Orari mercato LS-TC (come avevi tu)
MARKET_HOURS = {
    "timezone": "Europe/Rome",
    "open": "07:20",
    "close": "23:00"
}

# Festività italiane fisse
FIXED_HOLIDAYS = [
    (1, 1), (4, 25), (5, 1), (6, 2), (8, 15), (12, 25), (12, 26)
]

def is_market_open(now = None):
    if now is None:
        now = DateTime.now()
    local = now.setZone(MARKET_HOURS["timezone"])

    # Weekend
    if local.weekday in [6, 7]:
        return False

    # Festività fisse
    if (local.month, local.day) in FIXED_HOLIDAYS:
        return False

    # Pasqua e Pasquetta (algoritmo semplificato, puoi espandere)
    year = local.year
    # (omesso per brevità, usa lo stesso algoritmo che avevi in config.js)

    # Orari
    open_time = local.set({ "hour": 7, "minute": 20 })
    close_time = local.set({ "hour": 23, "minute": 0 })
    return open_time <= local <= close_time