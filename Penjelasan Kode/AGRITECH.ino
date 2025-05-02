#include <WiFi.h>               // Library untuk koneksi WiFi
#include <DHT.h>                // Library untuk sensor suhu & kelembapan DHT
#include <HTTPClient.h>         // Library untuk melakukan request HTTP

// Kredensial WiFi
const char* ssid = "MASUKAN NAMA WIFI/HOSPOT ANDA";        // Nama jaringan WiFi
const char* password = "MASUKA PASSWORD ANDA";             // Password WiFi

// URL server Flask
const char* serverDataURL = "http://copy IPv4 Address anda/data";      // URL endpoint untuk data sensor
const char* serverPompaURL = "http://copy IPv4 Address anda/pompa/status"; // URL endpoint status pompa
const char* serverMLURL = "http://copy IPv4 Address anda/ML";          // URL endpoint untuk prediksi ML

// Penentuan pin
#define DHTPIN 4                 // Pin untuk sensor DHT
#define DHTTYPE DHT22           // Tipe sensor DHT
#define LDR_PIN 34              // Pin sensor cahaya (LDR)
#define HUJAN_PIN 32            // Pin sensor hujan
#define TANAH_PIN 35            // Pin sensor kelembapan tanah
#define RELAY_PIN 25            // Pin relay untuk kontrol pompa

DHT dht(DHTPIN, DHTTYPE);       // Inisialisasi objek DHT

void setup() {
  Serial.begin(115200);         // Memulai komunikasi serial dengan baud rate 115200
  
  pinMode(LDR_PIN, INPUT);      // Set pin LDR sebagai input
  pinMode(HUJAN_PIN, INPUT);    // Set pin hujan sebagai input
  pinMode(TANAH_PIN, INPUT);    // Set pin tanah sebagai input
  pinMode(RELAY_PIN, OUTPUT);   // Set pin relay sebagai output
  
  digitalWrite(RELAY_PIN, LOW); // Matikan pompa pada awalnya
  
  dht.begin();                  // Inisialisasi sensor DHT

  WiFi.begin(ssid, password);   // Mulai koneksi ke WiFi
  Serial.println("Menghubungkan WiFi...");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);                 // Tunggu 500ms setiap cek koneksi
    Serial.print(".");          // Tampilkan titik sebagai indikator menunggu
  }
  Serial.println("\nWiFi Terhubung!"); // WiFi berhasil terhubung
}

// Fungsi untuk mapping float (seperti map untuk int tapi hasil float)
float mapFloat(float x, float in_min, float in_max, float out_min, float out_max) {
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

// Fungsi untuk membulatkan angka ke 1 angka desimal
float round1(float value) {
    return round(value * 10) / 10.0;
}

void loop() {
  float suhu = dht.readTemperature();          // Baca suhu dari sensor DHT
  float kelembapanUdara = dht.readHumidity();  // Baca kelembapan udara dari DHT

  if (isnan(suhu) || isnan(kelembapanUdara)) { // Jika pembacaan gagal
    Serial.println("Sensor DHT error!");       // Tampilkan error
    return;                                    // Keluar dari loop
  } 

  suhu = round1(suhu);                         // Bulatkan suhu ke 1 desimal
  kelembapanUdara = round1(kelembapanUdara);   // Bulatkan kelembapan udara ke 1 desimal

  int cahayaValue = analogRead(LDR_PIN);       // Baca nilai cahaya (ADC)
  int hujanValue = analogRead(HUJAN_PIN);      // Baca nilai sensor hujan (ADC)
  int kelembapanTanahValue = analogRead(TANAH_PIN); // Baca nilai kelembapan tanah (ADC)

  // Ubah nilai sensor ke dalam persentase
  int cahayaPercent = map(cahayaValue, 0, 4095, 100, 0);          // Terang = nilai kecil
  int kelembapanTanahPercent = map(kelembapanTanahValue, 4095, 0, 0, 100); // Tanah basah = nilai besar
  int hujanPercent = map(hujanValue, 0, 4095, 100, 0);            // Hujan deras = nilai kecil

  // Mapping untuk mendapatkan nilai real berdasarkan karakteristik sensor
  float HumTanah = round1(mapFloat(kelembapanTanahValue, 4095, 0, 15.0, 90.0)); // Estimasi RH tanah
  float hujanV = round1(mapFloat(hujanValue, 0, 4095, 298.6, 20.2));            // Estimasi intensitas hujan

  if (WiFi.status() == WL_CONNECTED) {       // Jika WiFi terhubung
    Serial.println("Kirim data sensor...");

    HTTPClient http;                         // Buat objek HTTP
    http.begin(serverDataURL);               // Mulai koneksi ke server data
    http.addHeader("Content-Type", "application/json"); // Set header JSON

    // Buat data JSON untuk dikirim
    String jsonData = "{";
    jsonData += "\"cahaya\":" + String(cahayaPercent) + ",";
    jsonData += "\"suhu\":" + String(suhu) + ",";
    jsonData += "\"kelembapan_udara\":" + String(kelembapanUdara) + ",";
    jsonData += "\"hujan\":" + String(hujanPercent) + ",";
    jsonData += "\"kelembapan_tanah\":" + String(kelembapanTanahPercent);
    jsonData += "}";

    int httpResponseCode = http.POST(jsonData); // Kirim data POST ke server

    if (httpResponseCode > 0) {
      String response = http.getString();     // Ambil respon dari server
      Serial.println("Server response: " + response);
    } else {
      Serial.println("Error kirim data: " + String(httpResponseCode)); // Tampilkan error jika gagal
    }
    http.end();                               // Akhiri koneksi HTTP

    HTTPClient pompaHttp;
    pompaHttp.begin(serverPompaURL);         // Mulai koneksi ke server status pompa
    int pompaResponse = pompaHttp.GET();     // Ambil status pompa (GET)

    if (pompaResponse == 200) {
      String pompaStatus = pompaHttp.getString(); // Ambil isi respon
      pompaStatus.trim();                         // Hilangkan spasi tak perlu
      Serial.println("Status Pompa: " + pompaStatus);

      digitalWrite(RELAY_PIN, pompaStatus == "ON" ? LOW : HIGH); // ON = aktifkan pompa (LOW)
    } else {
      Serial.println("Gagal mengambil status pompa");
    }
    pompaHttp.end();                        // Tutup koneksi HTTP

    HTTPClient MLhttp;
    MLhttp.begin(serverMLURL);              // Mulai koneksi ke server ML
    MLhttp.addHeader("Content-Type", "application/json");

    // Buat data JSON untuk prediksi ML
    String jsonML = "{";
    jsonML += "\"suhu\":" + String(suhu) + ",";
    jsonML += "\"kelembapan_udara\":" + String(kelembapanUdara) + ",";
    jsonML += "\"hujanV\":" + String(hujanV) + ",";
    jsonML += "\"humtanah\":" + String(HumTanah);
    jsonML += "}";

    int MLhttpResponseCode = MLhttp.POST(jsonML); // Kirim data ke server ML

    if (MLhttpResponseCode > 0) {
      String mlResponse = MLhttp.getString(); // Ambil respon dari server ML
      Serial.println("ML Prediction: " + mlResponse);
    } else {
      Serial.println("Error ML request: " + String(MLhttpResponseCode));
    }
    
    MLhttp.end();                           // Akhiri koneksi HTTP
  } else {
    Serial.println("WiFi putus, reconnect..."); // Jika WiFi terputus
    WiFi.begin(ssid, password);                 // Coba sambungkan ulang
  } 

  // Tampilkan data sensor ke Serial Monitor
  Serial.println("Suhu: " + String(suhu) + 
               " Hum: " + String(kelembapanUdara) + 
               " Cahaya: " + String(cahayaPercent) + 
               " HumTanah: " + String(kelembapanTanahPercent) + 
               " Hujan: " + String(hujanPercent)
               );

  delay(2000); // Tunggu 2 detik sebelum loop selanjutnya
}
