#ifndef CONFIG_H
#define CONFIG_H

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