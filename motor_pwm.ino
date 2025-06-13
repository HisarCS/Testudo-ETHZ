// Motor A pins
#define AIN1 26
#define AIN2 27
#define PWMA 14
#define STBY 25

// No need for custom analogWrite - ESP32 Arduino core 3.x includes it!

void setup() {
  pinMode(AIN1, OUTPUT);
  pinMode(AIN2, OUTPUT);
  pinMode(PWMA, OUTPUT);
  pinMode(STBY, OUTPUT);

  digitalWrite(STBY, HIGH); // Enable motor driver
}

void loop() {
  // 🔄 Forward at 50% speed
  digitalWrite(AIN1, HIGH);
  digitalWrite(AIN2, LOW);
  analogWrite(PWMA, 128);  // 50% duty cycle
  delay(2000);

  // 🛑 Stop
  analogWrite(PWMA, 0);
  delay(1000);

  // 🔁 Backward at full speed
  digitalWrite(AIN1, LOW);
  digitalWrite(AIN2, HIGH);
  analogWrite(PWMA, 255);  // 100% duty cycle
  delay(2000);

  // 🛑 Stop again
  analogWrite(PWMA, 0);
  delay(1000);
}
