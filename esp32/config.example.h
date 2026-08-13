#ifndef CONFIG_H
#define CONFIG_H

#define LANG_IT 1
#define LANG_EN 2
#define LANG_ES 3
#define LANG_DE 4
#define LANG_FR 5



// Select active language
// Choose one from available options: LANG_IT, LANG_EN, LANG_ES, LANG_DE, LANG_FR
#define CURRENT_LANG LANG_IT

// Enter your credentials here and rename this file to config.h
// NOTE: if you only have 1 or 2 Wi-Fi networks, just enter the same credentials in the remaining fields.
const char* ssid_home    = "YOUR_HOME_SSID";
const char* pass_home    = "YOUR_HOME_PASSWORD";

const char* ssid_office  = "YOUR_OFFICE_SSID";
const char* pass_office  = "YOUR_OFFICE_PASSWORD";

const char* ssid_hotspot = "YOUR_HOTSPOT_SSID";
const char* pass_hotspot = "YOUR_HOTSPOT_PASSWORD";

// Enter the raw URL of your hosted market.example.json file (GitHub, AWS, VPS, etc.)
const char* serverUrl = "https://raw.githubusercontent.com/username/repo/main/folder/market.example.json";

#endif