# utils//colors.h
----------------------------------------
#ifndef COLORS_H
#define COLORS_H

// Definizione colori logici → valori GRB corretti per il tuo LED

// Colori primari
#define LED_ROSSO   0,255,0     // Rosso logico → appare rosso
#define LED_VERDE   255,0,0     // Verde logico → appare verde
#define LED_BLU     0,0,255     // Blu/Azzurro → appare blu

// Colori secondari
#define LED_GIALLO  255,255,0   // Rosso+Verde → appare giallo
#define LED_CIANO   255,0,255   // Verde+Blu → appare ciano
#define LED_FUCSIA  0,255,255   // Rosso+Blu → appare fucsia
#define LED_BIANCO  255,255,255 // Tutti accesi → bianco
#define LED_NERO    0,0,0       // Tutti spenti → nero

// Alcuni extra utili
#define LED_VIOLA   0,128,128   // Viola scuro
#define LED_OLIVA   128,128,0   // Oliva
#define LED_AZZURRO 0,0,200     // Azzurro più tenue

#endif

# utils//holidays.py
----------------------------------------
from datetime import date

def easter_date(year):
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)

def is_holiday(d):
    fixed = [(1,1), (4,25), (5,1), (6,2), (8,15), (12,25), (12,26)]
    if (d.month, d.day) in fixed:
        return True
    easter = easter_date(d.year)
    if d == easter or d == easter + timedelta(days=1):
        return True
    return False

# utils//logger.py
----------------------------------------
from datetime import datetime

def log_info(msg):
    print(f"[{datetime.now().isoformat()}] INFO {msg}")

def log_error(msg):
    print(f"[{datetime.now().isoformat()}] ERROR {msg}")

