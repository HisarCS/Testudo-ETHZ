#define DAC_PIN 25  // Use GPIO25 or GPIO26

const int sampleRate = 8000;
const float frequency = 440.0;  // A4 note
const float amplitude = 127.0;
const float pi = 3.14159265;

void setup() {
  Serial.begin(115200);
}

void loop() {
  for (int i = 0; i < sampleRate; i++) {
    float theta = 2.0 * pi * frequency * i / sampleRate;
    int value = (int)(amplitude * sin(theta) + 128);  // DAC range: 0–255
    dacWrite(DAC_PIN, value);
    delayMicroseconds(1000000 / sampleRate);
  }
}
