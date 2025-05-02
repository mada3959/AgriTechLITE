#include <WiFi.h>
#include <DHT.h>
#include <HTTPClient.h>

// Wifi credentials
const char* ssid = "trinitrotoluene";
const char* password = "albedoye";

// Server Flask
const char* serverDataURL = "http://192.168.110.5:5000/data";
const char* serverPompaURL = "http://192.168.110.5:5000/pompa/status";
const char* serverMLURL = "http://192.168.110.5:5000/ML";

// Pin assignment
#define DHTPIN 4
#define DHTTYPE DHT22
#define LDR_PIN 34        // ADC1_CHANNEL_6
#define HUJAN_PIN 32
#define TANAH_PIN 35      // ADC1_CHANNEL_7
#define RELAY_PIN 25

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(115200);
  
  pinMode(LDR_PIN, INPUT);
  pinMode(HUJAN_PIN, INPUT);
  pinMode(TANAH_PIN, INPUT);
  pinMode(RELAY_PIN, OUTPUT);
  
  digitalWrite(RELAY_PIN, LOW); // Matikan pompa saat awal
  
  dht.begin();

  WiFi.begin(ssid, password);
  Serial.println("Menghubungkan WiFi...");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Terhubung!");
}

float mapFloat(float x, float in_min, float in_max, float out_min, float out_max) {
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

float round1(float value) {
    return round(value * 10) / 10.0;
}

void loop() {
  float suhu = dht.readTemperature();
  float kelembapanUdara = dht.readHumidity();

  if (isnan(suhu) || isnan(kelembapanUdara)) {
    Serial.println("Sensor DHT error!");
    return;
  } 

  suhu = round1(suhu);
  kelembapanUdara = round1(kelembapanUdara);

  int cahayaValue = analogRead(LDR_PIN);
  int hujanValue = analogRead(HUJAN_PIN);
  int kelembapanTanahValue = analogRead(TANAH_PIN);

  // Normalisasi hasil pembacaan (0-100%)
  int cahayaPercent = map(cahayaValue, 0, 4095, 100, 0);
  int kelembapanTanahPercent = map(kelembapanTanahValue, 4095, 0, 0, 100); 
  int hujanPercent = map(hujanValue, 0, 4095, 100, 0);

  // Mapping ke skala aslinya, lalu dibulatkan
  float HumTanah = round1(mapFloat(kelembapanTanahValue, 4095, 0, 15.0, 90.0));
  float hujanV = round1(mapFloat(hujanValue, 0, 4095, 298.6, 20.2));

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("Kirim data sensor...");

    HTTPClient http;
    http.begin(serverDataURL);
    http.addHeader("Content-Type", "application/json");

    String jsonData = "{";
    jsonData += "\"cahaya\":" + String(cahayaPercent) + ",";
    jsonData += "\"suhu\":" + String(suhu) + ",";
    jsonData += "\"kelembapan_udara\":" + String(kelembapanUdara) + ",";
    jsonData += "\"hujan\":" + String(hujanPercent) + ",";
    jsonData += "\"kelembapan_tanah\":" + String(kelembapanTanahPercent);
    jsonData += "}";

    int httpResponseCode = http.POST(jsonData);

    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("Server response: " + response);
    } else {
      Serial.println("Error kirim data: " + String(httpResponseCode));
    }
    http.end();

    HTTPClient pompaHttp;
    pompaHttp.begin(serverPompaURL);
    int pompaResponse = pompaHttp.GET();

    if (pompaResponse == 200) {
      String pompaStatus = pompaHttp.getString();
      pompaStatus.trim();
      Serial.println("Status Pompa: " + pompaStatus);

      digitalWrite(RELAY_PIN, pompaStatus == "ON" ? LOW : HIGH);
    } else {
      Serial.println("Gagal mengambil status pompa");
    }
    pompaHttp.end();

    HTTPClient MLhttp;
    MLhttp.begin(serverMLURL);
    MLhttp.addHeader("Content-Type", "application/json");

    String jsonML = "{";
    jsonML += "\"suhu\":" + String(suhu) + ",";
    jsonML += "\"kelembapan_udara\":" + String(kelembapanUdara) + ",";
    jsonML += "\"hujanV\":" + String(hujanV) + ",";
    jsonML += "\"humtanah\":" + String(HumTanah);
    jsonML += "}";

    int MLhttpResponseCode = MLhttp.POST(jsonML);

    if (MLhttpResponseCode > 0) {
      String mlResponse = MLhttp.getString();
      Serial.println("ML Prediction: " + mlResponse);
    } else {
      Serial.println("Error ML request: " + String(MLhttpResponseCode));
    }
    
    MLhttp.end();

  } else {
    Serial.println("WiFi putus, reconnect...");
    WiFi.begin(ssid, password);
  } 
  Serial.println("Suhu: " + String(suhu) + 
               " Hum: " + String(kelembapanUdara) + 
               " Cahaya: " + String(cahayaPercent) + 
               " HumTanah: " + String(kelembapanTanahPercent) + 
               " Hujan: " + String(hujanPercent)
               );

  delay(2000);
}
