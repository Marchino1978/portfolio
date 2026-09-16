#pragma once
#include <WiFi.h>

// ============================================================
// WIFI MANAGER
// ============================================================

enum class LedState;
void ledStatusSetState(LedState state);

enum WifiState {
  WIFI_IDLE,
  WIFI_CONNECTING_HOME,
  WIFI_CONNECTING_OFFICE,
  WIFI_CONNECTING_HOTSPOT,
  WIFI_CONNECTED,
  WIFI_FAIL
};

static WifiState wifiState = WIFI_IDLE;
static unsigned long wifiAttemptStart = 0;
static unsigned long lastWifiRetry    = 0;
static const unsigned long wifiTimeoutMs    = 15000;
static const unsigned long wifiRetryDelayMs = 30000;

static void wifiManagerStart(const char* ssid, const char* pass, WifiState nextState) {
  WiFi.disconnect(true, true);
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(ssid, pass);

  wifiAttemptStart = millis();
  wifiState = nextState;

  ledStatusSetState(LedState::BOOT_WIFI_SEARCH);

  Serial.printf("[WIFI] Connecting to %s...\n", ssid);
}

void wifiManagerSetup() {
  wifiState = WIFI_IDLE;
}

bool wifiManagerIsConnected() {
  return wifiState == WIFI_CONNECTED && WiFi.status() == WL_CONNECTED;
}

void ntpSyncNow();

void wifiManagerLoop() {
  wl_status_t st = WiFi.status();

  switch (wifiState) {

    case WIFI_IDLE:
      wifiManagerStart(ssid_home, pass_home, WIFI_CONNECTING_HOME);
      break;

    case WIFI_CONNECTING_HOME:
      if (st == WL_CONNECTED) {
        Serial.println(F("[WIFI] Connected (home)."));
        wifiState = WIFI_CONNECTED;
        ledStatusSetState(LedState::WIFI_CONNECTED);
        ntpSyncNow();
      } else if (millis() - wifiAttemptStart > wifiTimeoutMs) {
        wifiManagerStart(ssid_office, pass_office, WIFI_CONNECTING_OFFICE);
      }
      break;

    case WIFI_CONNECTING_OFFICE:
      if (st == WL_CONNECTED) {
        Serial.println(F("[WIFI] Connected (office)."));
        wifiState = WIFI_CONNECTED;
        ledStatusSetState(LedState::WIFI_CONNECTED);
        ntpSyncNow();
      } else if (millis() - wifiAttemptStart > wifiTimeoutMs) {
        wifiManagerStart(ssid_hotspot, pass_hotspot, WIFI_CONNECTING_HOTSPOT);
      }
      break;

    case WIFI_CONNECTING_HOTSPOT:
      if (st == WL_CONNECTED) {
        Serial.println(F("[WIFI] Connected (hotspot)."));
        wifiState = WIFI_CONNECTED;
        ledStatusSetState(LedState::WIFI_CONNECTED);
        ntpSyncNow();
      } else if (millis() - wifiAttemptStart > wifiTimeoutMs) {
        Serial.println(F("[WIFI] All SSIDs failed."));
        wifiState = WIFI_FAIL;
        lastWifiRetry = millis();
        ledStatusSetState(LedState::ERROR_WARNING);
      }
      break;

    case WIFI_CONNECTED:
      if (st != WL_CONNECTED) {
        Serial.println(F("[WIFI] Connection lost."));
        wifiState = WIFI_FAIL;
        lastWifiRetry = millis();
        ledStatusSetState(LedState::ERROR_WARNING);
      }
      break;

    case WIFI_FAIL:
      if (millis() - lastWifiRetry > wifiRetryDelayMs) {
        wifiManagerStart(ssid_home, pass_home, WIFI_CONNECTING_HOME);
      }
      break;
  }
}