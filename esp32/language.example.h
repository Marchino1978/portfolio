#pragma once
#include "config.h"

// ======================================================
// 1. IT
// ======================================================
#if CURRENT_LANG == LANG_IT

  #define TXT_WIFI_CONN       "Connessione WiFi..."
  #define TXT_TRY_HOME        "Provo CASA..."
  #define TXT_TRY_OFFICE      "Provo UFFICIO..."
  #define TXT_TRY_HOTSPOT     "Provo HOTSPOT..."
  
  #define TXT_WIFI_OK_HOME    "WiFi OK (CASA)"
  #define TXT_WIFI_OK_OFFICE  "WiFi OK (UFFICIO)"
  #define TXT_WIFI_OK_HOTSPOT "WiFi OK (HOTSPOT)"
  #define TXT_WIFI_FAIL       "WiFi FAIL"
  #define TXT_WIFI_LOST       "Connessione persa"

  #define TXT_NTP_CONN        "Connessione server NTP..."
  #define TXT_NTP_FAIL        "NTP FAIL"
  #define TXT_NTP_OK          "Connessione NTP OK"
  #define TXT_TIME_LABEL      "Sono le ore: %02d:%02d"

// ======================================================
// 2. EN
// ======================================================
#elif CURRENT_LANG == LANG_EN

  #define TXT_WIFI_CONN       "Connecting WiFi..."
  #define TXT_TRY_HOME        "Trying HOME..."
  #define TXT_TRY_OFFICE      "Trying OFFICE..."
  #define TXT_TRY_HOTSPOT     "Trying HOTSPOT..."
  
  #define TXT_WIFI_OK_HOME    "WiFi OK (HOME)"
  #define TXT_WIFI_OK_OFFICE  "WiFi OK (OFFICE)"
  #define TXT_WIFI_OK_HOTSPOT "WiFi OK (HOTSPOT)"
  #define TXT_WIFI_FAIL       "WiFi FAIL"
  #define TXT_WIFI_LOST       "Connection lost"

  #define TXT_NTP_CONN        "Connecting NTP server..."
  #define TXT_NTP_FAIL        "NTP FAIL"
  #define TXT_NTP_OK          "NTP Sync OK"
  #define TXT_TIME_LABEL      "Time: %02d:%02d"

// ======================================================
// 3. ES
// ======================================================
#elif CURRENT_LANG == LANG_ES

  #define TXT_WIFI_CONN       "Conectando WiFi..."
  #define TXT_TRY_HOME        "Probando CASA..."
  #define TXT_TRY_OFFICE      "Probando OFICINA..."
  #define TXT_TRY_HOTSPOT     "Probando HOTSPOT..."
  
  #define TXT_WIFI_OK_HOME    "WiFi OK (CASA)"
  #define TXT_WIFI_OK_OFFICE  "WiFi OK (OFICINA)"
  #define TXT_WIFI_OK_HOTSPOT "WiFi OK (HOTSPOT)"
  #define TXT_WIFI_FAIL       "WiFi ERROR"
  #define TXT_WIFI_LOST       "Conexion perdida"

  #define TXT_NTP_CONN        "Conectando NTP..."
  #define TXT_NTP_FAIL        "NTP ERROR"
  #define TXT_NTP_OK          "NTP Sincronizado"
  #define TXT_TIME_LABEL      "Hora: %02d:%02d"

// ======================================================
// 4. DE
// ======================================================
#elif CURRENT_LANG == LANG_DE

  #define TXT_WIFI_CONN       "WLAN Verbinden..."
  #define TXT_TRY_HOME        "Verbinde ZUHAUSE..."
  #define TXT_TRY_OFFICE      "Verbinde BURO..."
  #define TXT_TRY_HOTSPOT     "Verbinde HOTSPOT..."
  
  #define TXT_WIFI_OK_HOME    "WLAN OK (ZUHAUSE)"
  #define TXT_WIFI_OK_OFFICE  "WLAN OK (BURO)"
  #define TXT_WIFI_OK_HOTSPOT "WLAN OK (HOTSPOT)"
  #define TXT_WIFI_FAIL       "WLAN FEHLER"
  #define TXT_WIFI_LOST       "Verbindung getrennt"

  #define TXT_NTP_CONN        "NTP-Server Verbinden..."
  #define TXT_NTP_FAIL        "NTP FEHLER"
  #define TXT_NTP_OK          "NTP Zeit Sync OK"
  #define TXT_TIME_LABEL      "Uhrzeit: %02d:%02d"

// ======================================================
// 5. FR
// ======================================================
#elif CURRENT_LANG == LANG_FR

  #define TXT_WIFI_CONN       "Connexion WiFi..."
  #define TXT_TRY_HOME        "Essai MAISON..."
  #define TXT_TRY_OFFICE      "Essai BUREAU..."
  #define TXT_TRY_HOTSPOT     "Essai HOTSPOT..."
  
  #define TXT_WIFI_OK_HOME    "WiFi OK (MAISON)"
  #define TXT_WIFI_OK_OFFICE  "WiFi OK (BUREAU)"
  #define TXT_WIFI_OK_HOTSPOT "WiFi OK (HOTSPOT)"
  #define TXT_WIFI_FAIL       "WiFi ERREUR"
  #define TXT_WIFI_LOST       "Connexion perdue"

  #define TXT_NTP_CONN        "Connexion serv. NTP..."
  #define TXT_NTP_FAIL        "NTP ERREUR"
  #define TXT_NTP_OK          "NTP Synchronise"
  #define TXT_TIME_LABEL      "Il est: %02d:%02d"

// ======================================================
// FALLBACK: IT
// ======================================================
#else

  #define TXT_WIFI_CONN       "Connessione WiFi..."
  #define TXT_TRY_HOME        "Provo CASA..."
  #define TXT_TRY_OFFICE      "Provo UFFICIO..."
  #define TXT_TRY_HOTSPOT     "Provo HOTSPOT..."
  
  #define TXT_WIFI_OK_HOME    "WiFi OK (CASA)"
  #define TXT_WIFI_OK_OFFICE  "WiFi OK (UFFICIO)"
  #define TXT_WIFI_OK_HOTSPOT "WiFi OK (HOTSPOT)"
  #define TXT_WIFI_FAIL       "WiFi FAIL"
  #define TXT_WIFI_LOST       "Connessione persa"

  #define TXT_NTP_CONN        "Connessione server NTP..."
  #define TXT_NTP_FAIL        "NTP FAIL"
  #define TXT_NTP_OK          "Connessione NTP OK"
  #define TXT_TIME_LABEL      "Sono le ore: %02d:%02d"

#endif