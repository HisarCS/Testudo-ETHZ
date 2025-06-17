#include <Arduino.h>
#include <driver/i2s.h>
#include <SPIFFS.h>
#include <WebServer.h>
#include <WiFi.h>
#include <algorithm>
#include "driver/dac.h"


// === WiFi Credentials ===
const char* ssid = "Hisar_Superbox";
const char* password = "P@ssw0rd";

// === I2S Mic Pins ===
const int I2S_WS  = 17;
const int I2S_SCK = 26;
const int I2S_SD  = 32;

// === Audio Settings ===
const uint32_t SAMPLE_RATE     = 16000;
const uint16_t BITS_PER_SAMPLE = 16;
const uint8_t  CHANNELS        = 1;
const uint32_t RECORD_SECONDS  = 5;
const size_t   BUFFER_SIZE     = 512;

i2s_port_t I2S_PORT = I2S_NUM_0;
WebServer server(80);

// === WAV Header Writer ===
void writeWavHeader(File &file, uint32_t dataSize) {
  uint32_t chunkSize = 36 + dataSize;
  uint32_t byteRate = SAMPLE_RATE * CHANNELS * (BITS_PER_SAMPLE / 8);
  uint16_t blockAlign = CHANNELS * (BITS_PER_SAMPLE / 8);
  uint16_t audioFormat = 1;

  file.write((const uint8_t *)"RIFF", 4);
  file.write((uint8_t *)&chunkSize, 4);
  file.write((const uint8_t *)"WAVE", 4);
  file.write((const uint8_t *)"fmt ", 4);
  uint32_t subchunk1Size = 16;
  file.write((uint8_t *)&subchunk1Size, 4);
  file.write((uint8_t *)&audioFormat, 2);
  file.write((uint8_t *)&CHANNELS, 2);
  file.write((uint8_t *)&SAMPLE_RATE, 4);
  file.write((uint8_t *)&byteRate, 4);
  file.write((uint8_t *)&blockAlign, 2);
  file.write((uint8_t *)&BITS_PER_SAMPLE, 2);
  file.write((const uint8_t *)"data", 4);
  file.write((uint8_t *)&dataSize, 4);
}

// === I2S Setup ===
void setupI2S() {
  i2s_config_t config = {
    .mode = i2s_mode_t(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = i2s_bits_per_sample_t(BITS_PER_SAMPLE),
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = 256,
    .use_apll = false,
    .tx_desc_auto_clear = false,
    .fixed_mclk = 0
  };

  i2s_pin_config_t pins = {
    .bck_io_num = I2S_SCK,
    .ws_io_num = I2S_WS,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = I2S_SD
  };

  i2s_driver_install(I2S_PORT, &config, 0, NULL);
  i2s_set_pin(I2S_PORT, &pins);
  i2s_zero_dma_buffer(I2S_PORT);
}

// === Recording Function ===
void recordToWav(const char* filename) {
  File file = SPIFFS.open(filename, FILE_WRITE);
  if (!file) {
    Serial.println("❌ Failed to open file");
    return;
  }

  for (int i = 0; i < 44; i++) file.write((uint8_t)0);

  uint8_t buffer[BUFFER_SIZE];
  uint32_t totalBytes = SAMPLE_RATE * RECORD_SECONDS * (BITS_PER_SAMPLE / 8);
  uint32_t bytesWritten = 0;

  Serial.println("🎙️ Recording...");

  while (bytesWritten < totalBytes) {
    size_t toRead = std::min<size_t>(BUFFER_SIZE, static_cast<size_t>(totalBytes - bytesWritten));
    size_t bytesRead;
    i2s_read(I2S_PORT, buffer, toRead, &bytesRead, portMAX_DELAY);
    file.write(buffer, bytesRead);
    bytesWritten += bytesRead;
  }

  file.seek(0);
  writeWavHeader(file, bytesWritten);
  file.close();

  Serial.println("✅ Saved as /deneme.wav");
}

// === Web Server Handlers ===
void startWebServer() {
  server.on("/", HTTP_GET, []() {
    String ip = WiFi.localIP().toString();
    String html = "<h2>🟢 Web Server Running</h2>";
    html += "<p>IP: <b>" + ip + "</b></p>";
    html += "<p><a href='/deneme.wav'>🎧 Download deneme.wav</a></p>";
    server.send(200, "text/html", html);
  });

  server.on("/deneme.wav", HTTP_GET, []() {
    File file = SPIFFS.open("/deneme.wav", "r");
    if (!file) {
      server.send(404, "text/plain", "WAV not found");
      return;
    }
    server.streamFile(file, "audio/wav");
    file.close();
  });

  server.on("/upload", HTTP_POST, handleUpload);  // ✅ ADD THIS LINE

  server.begin();
  Serial.println("🌐 Web server started");
}


void setup() {
  Serial.begin(115200);
  delay(500);

  // Connect Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("📶 Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
  }
  Serial.println();
  Serial.print("✅ Connected! IP: ");
  Serial.println(WiFi.localIP());

  // Init SPIFFS
  if (!SPIFFS.begin(true)) {
    Serial.println("❌ SPIFFS mount failed");
    return;
  }

  // Init I2S
  setupI2S();

  // Wait 3 sec, then record
  Serial.println("👂 Waiting for clap...");

while (true) {
  int16_t samples[BUFFER_SIZE / 2];
  size_t bytesRead;
  i2s_read(I2S_PORT, samples, BUFFER_SIZE, &bytesRead, portMAX_DELAY);
  int sampleCount = bytesRead / 2;

  double sumSquares = 0;
  for (int i = 0; i < sampleCount; i++) {
    sumSquares += samples[i] * samples[i];
  }

  double rms = sqrt(sumSquares / sampleCount);
  double dB = 20.0 * log10(rms);

  Serial.print("🔊 dB: ");
  Serial.println(dB, 2);

  if (dB > 80.0) {
    Serial.println("👏 Clap detected! Waiting 3 seconds...");
    delay(000);
    break;
  }

  delay(50); // slight delay for smoother reading
}

  recordToWav("/deneme.wav");

  // Start web server
  startWebServer();
}

void loop() {
  server.handleClient();

  // 👂 Wait for clap continuously
  int16_t samples[BUFFER_SIZE / 2];
  size_t bytesRead;
  i2s_read(I2S_PORT, samples, BUFFER_SIZE, &bytesRead, portMAX_DELAY);
  int sampleCount = bytesRead / 2;

  double sumSquares = 0;
  for (int i = 0; i < sampleCount; i++) {
    sumSquares += samples[i] * samples[i];
  }

  double rms = sqrt(sumSquares / sampleCount);
  double dB = 20.0 * log10(rms);

  Serial.print("🔊 dB: ");
  Serial.println(dB, 2);

  if (dB > 60.0) {
    Serial.println("👏 Clap detected! Waiting 3 seconds...");
    delay(0000);
    recordToWav("/deneme.wav");
  }

  delay(50); // small delay to avoid overload
}

// === TTS Upload Handler ===
void handleUpload() {
  if (!server.hasArg("plain")) {
    server.send(400, "text/plain", "No data received");
    return;
  }

  File f = SPIFFS.open("/response.wav", FILE_WRITE);
  if (!f) {
    server.send(500, "text/plain", "Failed to open file for writing");
    return;
  }

  f.print(server.arg("plain")); // write raw data
  f.close();

  Serial.println("📥 Received TTS file: /response.wav");
  server.send(200, "text/plain", "File received");
}

void playWav(const char* filename) {
  File file = SPIFFS.open(filename, FILE_READ);
  if (!file || file.size() < 44) {
    Serial.println("❌ Cannot open or invalid WAV file");
    return;
  }

  dac_output_enable(DAC_CHANNEL_1); // Enable DAC1 (GPIO 25)
  file.seek(44); // Skip WAV header

  Serial.println("🔈 Playing response.wav via DAC...");

  const int sampleRate = 16000; // Adjust this to your WAV sample rate
  const int delayUs = 1000000 / sampleRate; // ~62.5µs for 16kHz

  while (file.available()) {
    uint8_t sample = file.read(); // 8-bit unsigned PCM
    dac_output_voltage(DAC_CHANNEL_1, sample);
    delayMicroseconds(delayUs);
  }

  file.close();
  Serial.println("✅ Playback finished.");
}
