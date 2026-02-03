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