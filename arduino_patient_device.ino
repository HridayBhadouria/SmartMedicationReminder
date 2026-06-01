#include <Wire.h>
#include <SPI.h>
#include <WiFiNINA.h>
#include <PubSubClient.h>
#include <U8g2lib.h>
#include <RTClib.h>

#define BUTTON_PIN 2
#define WHITE_LED 5
#define GREEN_LED 6
#define RED_LED 7
#define BUZZER_PIN 8

char ssid[] = "YOUR_WIFI_NAME";
char pass[] = "YOUR_WIFI_PASSWORD";

const char mqttServer[] = "192.168.4.110";
const int mqttPort = 1883;

const char commandTopic[] = "medicine/command";
const char eventTopic[] = "medicine/event";

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
RTC_DS3231 rtc;

U8G2_SH1106_128X64_NONAME_F_4W_HW_SPI display(U8G2_R0, 4, 10, 9);

bool rtcFound = false;
bool reminderActive = false;
bool buzzerState = false;

unsigned long reminderStartMillis = 0;
unsigned long lastBeepMillis = 0;

const unsigned long alarmDuration = 20000;
const unsigned long beepInterval = 500;

void setup() {
  Serial.begin(9600);

  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(WHITE_LED, OUTPUT);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  allOutputsOff();
  display.begin();

  if (rtc.begin()) {
    rtcFound = true;
  }

  connectWiFi();
  connectMQTT();
  showIdleScreen();
  publishEvent("ARDUINO_READY");
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  if (!mqttClient.connected()) {
    connectMQTT();
  }

  mqttClient.loop();

  if (reminderActive) {
    pulseBuzzer();
    checkButton();

    if (millis() - reminderStartMillis >= alarmDuration) {
      markMissed();
    }
  }
}

void connectWiFi() {
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print("Connecting to WiFi: ");
    Serial.println(ssid);
    WiFi.begin(ssid, pass);
    delay(3000);
  }
  Serial.println("WiFi connected");
}

void connectMQTT() {
  mqttClient.setServer(mqttServer, mqttPort);
  mqttClient.setCallback(handleMqttMessage);

  while (!mqttClient.connected()) {
    Serial.println("Connecting to MQTT broker...");
    if (mqttClient.connect("ArduinoNano33IoTMedicationDevice")) {
      Serial.println("MQTT connected");
      mqttClient.subscribe(commandTopic);
      publishEvent("MQTT_CONNECTED");
    } else {
      Serial.print("MQTT failed, state: ");
      Serial.println(mqttClient.state());
      delay(3000);
    }
  }
}

void handleMqttMessage(char* topic, byte* payload, unsigned int length) {
  String message = "";

  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  if (message == "START") {
    startReminder();
  }
  else if (message == "STOP") {
    stopAlarm();
  }
}

void startReminder() {
  reminderActive = true;
  reminderStartMillis = millis();
  lastBeepMillis = millis();

  digitalWrite(WHITE_LED, HIGH);
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, LOW);

  showMessage("MEDICINE", "TIME", "Press button");
  publishEvent("REMINDER_STARTED");
}

void stopAlarm() {
  reminderActive = false;
  noTone(BUZZER_PIN);
  allOutputsOff();
  showIdleScreen();
  publishEvent("STOPPED");
}

void checkButton() {
  if (digitalRead(BUTTON_PIN) == LOW) {
    delay(50);
    if (digitalRead(BUTTON_PIN) == LOW) {
      markTaken();
      while (digitalRead(BUTTON_PIN) == LOW) {
        delay(10);
      }
    }
  }
}

void pulseBuzzer() {
  if (millis() - lastBeepMillis >= beepInterval) {
    buzzerState = !buzzerState;
    if (buzzerState) {
      tone(BUZZER_PIN, 1000);
    } else {
      noTone(BUZZER_PIN);
    }
    lastBeepMillis = millis();
  }
}

void markTaken() {
  reminderActive = false;
  noTone(BUZZER_PIN);
  digitalWrite(WHITE_LED, LOW);
  digitalWrite(GREEN_LED, HIGH);
  digitalWrite(RED_LED, LOW);
  showMessage("MEDICINE", "TAKEN", "Thank you");
  publishEvent("TAKEN");
}

void markMissed() {
  reminderActive = false;
  noTone(BUZZER_PIN);
  digitalWrite(WHITE_LED, LOW);
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, HIGH);
  showMessage("MISSED", "DOSE", "Not taken");
  publishEvent("MISSED");
}

void allOutputsOff() {
  digitalWrite(WHITE_LED, LOW);
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, LOW);
  noTone(BUZZER_PIN);
}

void showIdleScreen() {
  showMessage("SMART", "MEDICINE", "Ready");
}

void showMessage(String line1, String line2, String line3) {
  display.clearBuffer();
  display.setFont(u8g2_font_ncenB10_tr);
  display.drawStr(5, 18, line1.c_str());
  display.drawStr(5, 38, line2.c_str());
  display.drawStr(5, 58, line3.c_str());
  display.sendBuffer();
}

String getTimeText() {
  if (!rtcFound) {
    return "NO_RTC_TIME";
  }

  DateTime now = rtc.now();
  char buffer[25];
  sprintf(buffer, "%04d-%02d-%02d %02d:%02d:%02d", now.year(), now.month(), now.day(), now.hour(), now.minute(), now.second());
  return String(buffer);
}

void publishEvent(String eventName) {
  String message = eventName + "," + getTimeText();
  mqttClient.publish(eventTopic, message.c_str());
}
