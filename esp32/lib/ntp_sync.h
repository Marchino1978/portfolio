#pragma once
#include <time.h>

// ============================================================
// NTP SYNC
// ============================================================

enum class LedState;
void ledStatusSetState(LedState state);

#define NTP_TZ_STRING "CET-1CEST,M3.5.0,M10.5.0/3"

static bool ntpSynced = false;

void ntpSyncSetup() {
  ntpSynced = false;
}

bool ntpSyncNow() {
  Serial.println(F("[NTP] Syncing..."));
  ledStatusSetState(LedState::NTP_SYNC);
  configTzTime(NTP_TZ_STRING, "pool.ntp.org", "time.nist.gov");

  struct tm timeinfo;
  int attempts = 0;
  while (!getLocalTime(&timeinfo) && attempts < 20) {
    delay(200);
    attempts++;
  }

  if (!getLocalTime(&timeinfo)) {
    Serial.println(F("[NTP] Sync FAILED."));
    ntpSynced = false;
    ledStatusSetState(LedState::ERROR_WARNING);
    return false;
  }

  ntpSynced = true;
  Serial.printf("[NTP] Synced: %02d:%02d %02d/%02d/%04d\n",
                timeinfo.tm_hour, timeinfo.tm_min,
                timeinfo.tm_mday, timeinfo.tm_mon + 1, timeinfo.tm_year + 1900);
  return true;
}

String ntpGetFormattedTimestamp() {
  struct tm timeinfo;
  if (!ntpSynced || !getLocalTime(&timeinfo)) {
    return String("N/A");
  }
  char buf[32];
  snprintf(buf, sizeof(buf), "%02d:%02d %02d/%02d/%04d",
           timeinfo.tm_hour, timeinfo.tm_min,
           timeinfo.tm_mday, timeinfo.tm_mon + 1, timeinfo.tm_year + 1900);
  return String(buf);
}