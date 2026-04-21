// master_node.ino — FINAL (ESP-NOW → Raspberry Pi via UART)

#include <ESP8266WiFi.h>
#include <espnow.h>
#include <ArduinoJson.h>

typedef struct {
  uint8_t nodeId;
  char    ssid[33];
  char    bssid[18];
  int8_t  rssi;
  uint8_t channel;
  uint8_t encType;
  bool    isHidden;
} NetworkEntry;

const char* encTypeName(uint8_t enc, bool isHidden) {

  if (isHidden) return "HIDDEN";

  switch (enc) {
    case 0: return "OPEN";
    case 1: return "WEP";
    case 2: return "WPA";
    case 3: return "WPA2";
    case 4: return "WPA/WPA2";
    case 5: return "ENTERPRISE";
    case 6: return "WPA3";
    case 7: return "MODERN_SECURED";  // instead of guessing WPA2/WPA3
    case 255: return "ENTERPRISE/UNKNOWN";
    default: return "UNKNOWN";
  }
}

void onDataReceived(uint8_t *mac, uint8_t *data, uint8_t len) {
  if (len != sizeof(NetworkEntry)) return;

  NetworkEntry entry;
  memcpy(&entry, data, sizeof(entry));

  StaticJsonDocument<256> doc;
  doc["n"]  = entry.nodeId;
  doc["ss"] = entry.ssid;
  doc["bm"] = entry.bssid;
  doc["rs"] = entry.rssi;
  doc["ch"] = entry.channel;
  doc["en"] = encTypeName(entry.encType, entry.isHidden);
  doc["hi"] = entry.isHidden ? 1 : 0;

  // 👉 Send JSON to Raspberry Pi via UART
  serializeJson(doc, Serial);
  Serial.println();   // VERY IMPORTANT (newline for Python)

  Serial.print("[DEBUG] RAW ENC VALUE: ");
  Serial.println(entry.encType);
}

void setup() {
  Serial.begin(115200);   // MUST match Raspberry Pi baud

  WiFi.mode(WIFI_STA);
  WiFi.disconnect();

  if (esp_now_init() != 0) {
    Serial.println("ESP-NOW init failed — halting");
    while (true) delay(1000);
  }

  esp_now_set_self_role(ESP_NOW_ROLE_SLAVE);
  esp_now_register_recv_cb(onDataReceived);

  Serial.println("Master ready");
  Serial.print("My MAC: ");
  Serial.println(WiFi.macAddress());
}

void loop() {
  delay(10); // everything is callback-driven
}