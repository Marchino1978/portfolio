#pragma once

// ============================================================
// STATE MACHINE (FSM)
// ============================================================

enum class SystemState {
  BOOT,
  WIFI_CONNECT,
  IDLE,
  FREEZE
};

bool wifiManagerIsConnected();
enum class LedState;
void ledStatusSetState(LedState state);

static SystemState currentState = SystemState::BOOT;
static unsigned long freezeStartMillis = 0;
static unsigned long freezeDurationMs = 0;

inline void stateMachineSetup() {
  currentState = SystemState::BOOT;
}

inline SystemState stateMachineGetCurrent() {
  return currentState;
}

inline void stateMachineTriggerFreeze(bool extended) {
  freezeStartMillis = millis();
  freezeDurationMs = extended ? FREEZE_TIME_EXTENDED_MS : FREEZE_TIME_MS;
  currentState = SystemState::FREEZE;
}

inline void stateMachineLoop() {
  switch (currentState) {

    case SystemState::BOOT:
      currentState = SystemState::WIFI_CONNECT;
      break;

    case SystemState::WIFI_CONNECT:
      if (wifiManagerIsConnected()) {
        currentState = SystemState::IDLE;
        ledStatusSetState(LedState::IDLE);
      }
      break;

    case SystemState::IDLE:
      break;

    case SystemState::FREEZE:
      if (millis() - freezeStartMillis >= freezeDurationMs) {
        currentState = SystemState::IDLE;
        ledStatusSetState(LedState::IDLE);
      }
      break;
  }
}