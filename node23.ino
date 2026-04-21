// scanner_node.ino — Node 2 / Node 3
#include <ESP8266WiFi.h>
#include <espnow.h>

#define NODE_ID 2   // change to 3 for Node 3

// 👉 Replace with your MASTER node MAC address
uint8_t masterMAC[] = {0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF};

#pragma pack(push, 1)
typedef struct {
  uint8_t nodeId;
  char ssid[33];
  char bssid[18];
  int8_t rssi;
  uint8_t channel;
  uint8_t encType;
  bool isHidden;
} NetworkEntry;
#pragma pack(pop)

// ------------------ CALLBACK ------------------

void onSendCallback(uint8_t *mac, uint8_t status) {
  Serial.printf("Send status: %s\n", status == 0 ? "OK" : "FAIL");
}

// ------------------ SETUP ------------------

void setup() {
  Serial.begin(115200);

  WiFi.mode(WIFI_STA);
  WiFi.disconnect();

  if (esp_now_init() != 0) {
    Serial.println("ESP-NOW init failed");
    return;
  }

  esp_now_set_self_role(ESP_NOW_ROLE_CONTROLLER);
  esp_now_register_send_cb(onSendCallback);

  esp_now_add_peer(masterMAC, ESP_NOW_ROLE_SLAVE, 1, NULL, 0);

  Serial.println("Scanner Node Ready");
}

// ------------------ LOOP ------------------

void loop() {
  int count = WiFi.scanNetworks(false, true); // include hidden

  Serial.printf("Found %d networks\n", count);

  for (int i = 0; i < count; i++) {
    NetworkEntry entry;

    entry.nodeId   = NODE_ID;
    entry.rssi     = WiFi.RSSI(i);
    entry.channel  = WiFi.channel(i);
    entry.encType  = WiFi.encryptionType(i);
    entry.isHidden = (WiFi.SSID(i).length() == 0);

    strncpy(entry.ssid,
            entry.isHidden ? "[hidden]" : WiFi.SSID(i).c_str(),
            32);

    strncpy(entry.bssid,
            WiFi.BSSIDstr(i).c_str(),
            17);

    entry.ssid[32]  = '\0';
    entry.bssid[17] = '\0';

    esp_now_send(masterMAC, (uint8_t*)&entry, sizeof(entry));

    delay(20); // small gap
  }

  WiFi.scanDelete();

  delay(30000); // scan every 30 seconds
}