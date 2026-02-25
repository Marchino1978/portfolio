# esp32//ETF.ino
----------------------------------------
// ======================================================
//  SKETCH FINALE
// ======================================================
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <LovyanGFX.hpp>
#include <Adafruit_NeoPixel.h>
#include <time.h>

void wifiFadeEffect();
void appendNtpLine(const char* msg, int lineIndex);

#define LCD_BL 22
#define LED_PIN 8
#define NUMPIXELS 1

Adafruit_NeoPixel pixels(NUMPIXELS, LED_PIN, NEO_GRB + NEO_KHZ800);

const char* ssid_office  = "TIM-17040875";
const char* pass_office  = "verol2022$";
const char* ssid_home    = "linksys";
const char* pass_home    = "1123581321";
const char* ssid_hotspot = "HUAWEI P10";
const char* pass_hotspot = "qwerty123$";

const char* serverUrl = "https://raw.githubusercontent.com/Marchino1978/portfolio/main/data/market.json";

// ======================================================
//  DISPLAY LOVYANGFX
// ======================================================
class LGFX : public lgfx::LGFX_Device {
  lgfx::Panel_ST7789 _panel;
  lgfx::Bus_SPI _bus;

public:
  LGFX() {
    auto bcfg = _bus.config();
    bcfg.spi_host = SPI2_HOST;
    bcfg.spi_mode = 0;
    bcfg.freq_write = 40000000;
    bcfg.spi_3wire = true;
    bcfg.use_lock = true;
    bcfg.dma_channel = SPI_DMA_CH_AUTO;
    bcfg.pin_sclk = 7;
    bcfg.pin_mosi = 6;
    bcfg.pin_miso = -1;
    bcfg.pin_dc   = 15;
    _bus.config(bcfg);
    _panel.setBus(&_bus);

    auto pcfg = _panel.config();
    pcfg.pin_cs   = 14;
    pcfg.pin_rst  = 21;
    pcfg.panel_width  = 172;
    pcfg.panel_height = 320;
    pcfg.offset_x = 34;
    pcfg.offset_y = 0;
    pcfg.invert = true;
    pcfg.bus_shared = true;
    _panel.config(pcfg);

    setPanel(&_panel);
  }
};

LGFX display;
DynamicJsonDocument doc(4096);

// ======================================================
//  VARIABILI GLOBALI
// ======================================================
int currentETF = 0;
unsigned long lastSwitchETF = 0;
unsigned long lastUpdate    = 0;

// ======================================================
//  WIFI STATE MACHINE
// ======================================================
enum WifiState {
  WIFI_IDLE,
  WIFI_CONNECTING_HOME,
  WIFI_CONNECTING_OFFICE,
  WIFI_CONNECTING_HOTSPOT,
  WIFI_CONNECTED,
  WIFI_FAIL
};

WifiState wifiState = WIFI_IDLE;
unsigned long wifiAttemptStart = 0;
unsigned long lastWifiRetry    = 0;
const unsigned long wifiTimeoutMs     = 15000;
const unsigned long wifiRetryDelayMs  = 30000;

// ======================================================
//  FADE BLU DURANTE CONNESSIONE
// ======================================================
void wifiFadeEffect() {
  static unsigned long lastFade = 0;
  unsigned long now = millis();

  if (now - lastFade > 20) {
    lastFade = now;
    static bool fadeUp = true;
    static int fadeValue = 0;

    fadeValue += fadeUp ? 5 : -5;
    if (fadeValue >= 255) { fadeValue = 255; fadeUp = false;
    }
    if (fadeValue <= 0)   { fadeValue = 0;   fadeUp = true;
    }

    pixels.setPixelColor(0, pixels.Color(0, 0, fadeValue));
    pixels.show();
  }
}

// ======================================================
//  RIGHE TESTO WIFI + NTP
// ======================================================
void appendNtpLine(const char* msg, int lineIndex) {
  int y = 40 + lineIndex * 22;
  display.setCursor(10, y);
  display.setTextSize(2);
  display.setTextColor(TFT_BLUE);
  display.println(msg);
}

// ======================================================
//  SYNC NTP
// ======================================================
void syncNtp() {
  appendNtpLine("Connessione server NTP...", 3);
  delay(3000);
  configTzTime("CET-1CEST,M3.5.0,M10.5.0/3", "pool.ntp.org", "time.nist.gov");

  struct tm timeinfo;
  int tentativi = 0;
  while (!getLocalTime(&timeinfo) && tentativi < 20) {
    wifiFadeEffect();
    delay(200);
    tentativi++;
  }

  if (!getLocalTime(&timeinfo)) {
    appendNtpLine("NTP FAIL", 4);
    delay(3000);
    return;
  }

  appendNtpLine("Connessione NTP OK", 4);
  delay(3000);
  char ora[32];
  snprintf(ora, sizeof(ora), "Sono le ore: %02d:%02d", timeinfo.tm_hour, timeinfo.tm_min);
  appendNtpLine(ora, 5);

  unsigned long start = millis();
  while (millis() - start < 5000) {
    wifiFadeEffect();
    delay(20);
  }

  display.fillScreen(TFT_BLACK);
  pixels.setPixelColor(0, pixels.Color(0, 0, 0));
  pixels.show();
}

// ======================================================
//  AVVIO WIFI
// ======================================================
void wifiStart(const char* ssid, const char* pass, WifiState nextState, const char* msg) {
  WiFi.disconnect(true, true);
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(ssid, pass);

  wifiAttemptStart = millis();
  wifiState = nextState;

  display.fillScreen(TFT_BLACK);

  appendNtpLine("Connessione WiFi...", 0);
  appendNtpLine(msg, 1);

  delay(1000);
}

// ======================================================
//  FETCH DATI
// ======================================================
void fetchData() {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  http.begin(serverUrl);
  int httpCode = http.GET();

  if (httpCode == 200) {
    String payload = http.getString();
    deserializeJson(doc, payload);
  }

  http.end();
}

// ======================================================
//  UPDATE WIFI
// ======================================================
void wifiUpdateState() {
  wl_status_t st = WiFi.status();
  switch (wifiState) {

    case WIFI_IDLE:
      wifiStart(ssid_home, pass_home, WIFI_CONNECTING_HOME, "Provo CASA...");
      break;
    case WIFI_CONNECTING_HOME:
      if (st == WL_CONNECTED) {
        wifiState = WIFI_CONNECTED;
        appendNtpLine("WiFi OK (CASA)", 2);
        delay(3000);
        syncNtp();
        fetchData();
      } else if (millis() - wifiAttemptStart > wifiTimeoutMs) {
        wifiStart(ssid_office, pass_office, WIFI_CONNECTING_OFFICE, "Provo UFFICIO...");
      }
      break;

    case WIFI_CONNECTING_OFFICE:
      if (st == WL_CONNECTED) {
        wifiState = WIFI_CONNECTED;
        appendNtpLine("WiFi OK (UFFICIO)", 2);
        delay(3000);
        syncNtp();
        fetchData();
      } else if (millis() - wifiAttemptStart > wifiTimeoutMs) {
        wifiStart(ssid_hotspot, pass_hotspot, WIFI_CONNECTING_HOTSPOT, "Provo HOTSPOT...");
      }
      break;

    case WIFI_CONNECTING_HOTSPOT:
      if (st == WL_CONNECTED) {
        wifiState = WIFI_CONNECTED;
        appendNtpLine("WiFi OK (HOTSPOT)", 2);
        delay(3000);
        syncNtp();
        fetchData();
      } else if (millis() - wifiAttemptStart > wifiTimeoutMs) {
        wifiState = WIFI_FAIL;
        lastWifiRetry = millis();
        display.setTextColor(TFT_RED);
        display.setCursor(10, 40 + 2 * 22);
        display.setTextSize(2);
        display.println("WiFi FAIL");
      }
      break;
    case WIFI_CONNECTED:
      if (st != WL_CONNECTED) {
        wifiState = WIFI_FAIL;
        lastWifiRetry = millis();
        display.setTextColor(TFT_RED);
        display.setCursor(10, 40 + 2 * 22);
        display.setTextSize(2);
        display.println("Connessione persa");
      }
      break;
    case WIFI_FAIL:
      if (millis() - lastWifiRetry > wifiRetryDelayMs) {
        wifiStart(ssid_home, pass_home, WIFI_CONNECTING_HOME, "Provo CASA...");
      }
      break;
  }
}

// ======================================================
//  COMPACT VARIAZIONI
// ======================================================
void compactVar(const char* raw, char* out) {
  if (!raw || strcmp(raw, "N/A") == 0) {
    strcpy(out, "N/A");
    return;
  }

  char buf[32];
  strncpy(buf, raw, sizeof(buf));
  buf[31] = 0;

  char letter = 0;
  for (int i = strlen(buf) - 1; i >= 0; i--) {
    if (isalpha(buf[i])) {
      letter = buf[i];
      buf[i] = 0;
      break;
    }
  }

  char* p = strchr(buf, '%');
  if (p) *p = 0;

  if (buf[0] == '+' || buf[0] == '-') {
    memmove(buf, buf + 1, strlen(buf));
  }

  double val = atof(buf);

  if (letter) {
    if (val >= 10.0) {
      snprintf(out, 32, "%.1f%c", val, letter);
    } else {
      snprintf(out, 32, "%.2f%c", val, letter);
    }
  } else {
    if (val >= 10.0) {
      snprintf(out, 32, "%.1f", val);
    } else {
      snprintf(out, 32, "%.2f", val);
    }
  }
}

// ======================================================
//  COLORI VARIAZIONI
// ======================================================
int colorForVar(const char* raw) {
  if (!raw || strcmp(raw, "N/A") == 0) return TFT_CYAN;
  if (strchr(raw, '-') != nullptr) return TFT_RED;
  if (strstr(raw, "0.00") != nullptr) return TFT_WHITE;
  return TFT_GREEN;
}

// ======================================================
//  LED LOGIC
// ======================================================
void updateLed(const char* v1_raw, const char* v2_raw, const char* v3_raw, const char* v_led_raw, const char* marketStatus) {
  if (marketStatus && strcmp(marketStatus, "CHIUSO") == 0) {
    pixels.setPixelColor(0, pixels.Color(0, 0, 0));
    pixels.show();
    return;
  }

  bool anyNA = false;
  if (strcmp(v1_raw, "N/A") == 0) anyNA = true;
  if (strcmp(v2_raw, "N/A") == 0) anyNA = true;
  if (strcmp(v3_raw, "N/A") == 0) anyNA = true;
  if (strcmp(v_led_raw, "N/A") == 0) anyNA = true;

  if (anyNA) {
    // LED CIANO FISSO (GRB: 255, 0, 255 -> R=255, G=0, B=255)
    pixels.setPixelColor(0, pixels.Color(255, 0, 255)); 
    pixels.show();
    return;
  }

  if (strchr(v_led_raw, '-') != nullptr) {
    pixels.setPixelColor(0, pixels.Color(0, 255, 0)); // VERDE negativo
    pixels.show();
    return;
  }

  if (strstr(v_led_raw, "0.00") != nullptr) {
    pixels.setPixelColor(0, pixels.Color(0, 0, 0));
    pixels.show();
    return;
  }

  pixels.setPixelColor(0, pixels.Color(255, 0, 0)); // ROSSO positivo
  pixels.show();
}

// ======================================================
//  SPECIAL DAY
// ======================================================
bool isSpecialDate() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) return false;
  return (timeinfo.tm_mon + 1 == 4 && timeinfo.tm_mday == 22);
}

void drawSpecialDay(const char* marketStatus) {
  static bool firstDraw = true;
  if (firstDraw) {
    display.fillRect(0, 130, display.width(), display.height() - 130, TFT_BLACK);
    firstDraw = false;
  } else {
    display.fillRect(20, 140, 300, 40, TFT_BLACK);
  }

  static bool alt = false;
  static unsigned long lastToggle = 0;
  unsigned long now = millis();

  bool marketOpen = (marketStatus && strcmp(marketStatus, "APERTO") == 0);
  if (!marketOpen) {
    if (now - lastToggle > 1000) {
      alt = !alt;
      lastToggle = now;
    }
  } else {
    alt = true;
  }

  display.setCursor(20, 140);
  display.setTextSize(3);
  display.setTextColor(TFT_RED);
  if (alt) {
    display.print("HAPPY B-DAY");
  } else {
    display.print("MARKET CLOSED");
  }
}

// ======================================================
//  SHOW ETF
// ======================================================
void showETF(JsonObject etf, const char* marketStatus) {
  display.fillScreen(TFT_BLACK);

  const char* label = etf["label"] | etf["symbol"];
  float price       = etf["price"] | etf["value"];
  const char* v1_raw    = etf["v1"] | "N/A";
  const char* v2_raw    = etf["v2"] | "N/A";
  const char* v3_raw    = etf["v3"] | "N/A";
  const char* v_led_raw = etf["v_led"] | "N/A";

  char v1[32], v2[32], v3[32];
  compactVar(v1_raw, v1);
  compactVar(v2_raw, v2);
  compactVar(v3_raw, v3);

  bool marketClosed = (marketStatus && strcmp(marketStatus, "CHIUSO") == 0);
  static bool blink = false;
  static unsigned long lastBlink = 0;
  unsigned long now = millis();
  if (now - lastBlink > 500) {
    blink = !blink;
    lastBlink = now;
  }

  display.setCursor(10, 15);
  display.setTextSize(3);
  display.setTextColor(TFT_YELLOW);
  display.printf("%s", label);

  display.setCursor(10, 60);
  display.setTextSize(3);
  if (marketClosed) {
    display.setTextColor(blink ? TFT_YELLOW : TFT_BLACK);
    display.printf("Price: %.2fEUR", price);
  } else if (price <= 0) {
    display.setTextColor(TFT_CYAN);
    display.printf("Price: N/A");
  } else {
    display.setTextColor(TFT_WHITE);
    display.printf("Price: %.2fEUR", price);
  }

  display.setCursor(10, 105);
  display.setTextSize(3);
  display.setTextColor(strcmp(v1, "N/A") == 0 ? TFT_CYAN : colorForVar(v1_raw));
  display.print(v1);
  display.setTextColor(TFT_WHITE); display.print("|");
  display.setTextColor(strcmp(v2, "N/A") == 0 ? TFT_CYAN : colorForVar(v2_raw));
  display.print(v2);
  display.setTextColor(TFT_WHITE); display.print("|");
  display.setTextColor(strcmp(v3, "N/A") == 0 ? TFT_CYAN : colorForVar(v3_raw));
  display.print(v3);

  if (marketClosed) {
    display.setCursor(20, 150);
    display.setTextSize(3);
    display.setTextColor(TFT_RED);
    display.println("MARKET CLOSED");
  }

  updateLed(v1_raw, v2_raw, v3_raw, v_led_raw, marketStatus);
}

// ======================================================
//  REDRAW ETF
// ======================================================
void redrawCurrentETF() {
  const char* marketStatus = doc["status"] | "APERTO";

  JsonArray data = doc["values"]["data"].as<JsonArray>();
  if (data.size() == 0) return;
  if (currentETF >= data.size()) currentETF = 0;

  JsonObject etf = data[currentETF];
  showETF(etf, marketStatus);
  if (isSpecialDate()) {
    drawSpecialDay(marketStatus);
  }
}

// ======================================================
//  SETUP
// ======================================================
void setup() {
  Serial.begin(115200);

  pinMode(LCD_BL, OUTPUT);
  analogWrite(LCD_BL, 128);  // 50%

  display.init();
  display.setRotation(3);

  pixels.begin();
  pixels.setBrightness(50);
  pixels.clear();
  pixels.show();

  wifiState = WIFI_IDLE;
}

// ======================================================
//  LOOP
// ======================================================
void loop() {
  wifiUpdateState();
  if (wifiState != WIFI_CONNECTED) {
    wifiFadeEffect();
    delay(20);
    return;
  }

  unsigned long now = millis();
  bool dataUpdated = false;
  if (now - lastUpdate > 300000) {
    fetchData();
    lastUpdate = now;
    dataUpdated = true;
  }

  bool etfChanged = false;
  JsonArray data = doc["values"]["data"].as<JsonArray>();
  int totalETF = data.size();
  if (totalETF > 0 && now - lastSwitchETF > 15000) {
    currentETF = (currentETF + 1) % totalETF;
    lastSwitchETF = now;
    etfChanged = true;
  }

  const char* marketStatus = doc["status"] | "APERTO";
  bool marketClosed = (strcmp(marketStatus, "CHIUSO") == 0);
  static bool lastBlink = false;
  bool blinkChanged = false;
  if (marketClosed) {
    bool currentBlink = (now / 500) % 2;
    if (currentBlink != lastBlink) {
      blinkChanged = true;
      lastBlink = currentBlink;
    }
  }

  if (etfChanged || dataUpdated || blinkChanged) {
    redrawCurrentETF();
  }

  delay(20);
}

