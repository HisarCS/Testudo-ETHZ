#include <Adafruit_GFX.h>
#include <Adafruit_SSD1351.h>
#include <SPI.h>

// Pin definitions for ESP32-WROOM-32
#define SCLK 18
#define MOSI 23
#define DC   16
#define CS   5
#define RST  17

Adafruit_SSD1351 display = Adafruit_SSD1351(128, 128, &SPI, CS, DC, RST);

void setup() {
  Serial.begin(115200);
  display.begin();

  // Fill screen black
  display.fillScreen(0x0000);

  // Set text properties
  display.setCursor(5, 50);       // x, y position
  display.setTextColor(0xFFFF);   // White
  display.setTextSize(1);         // Text scale
  display.println("Kaan is gay");
}

void loop() {
  // Nothing to loop yet
}
