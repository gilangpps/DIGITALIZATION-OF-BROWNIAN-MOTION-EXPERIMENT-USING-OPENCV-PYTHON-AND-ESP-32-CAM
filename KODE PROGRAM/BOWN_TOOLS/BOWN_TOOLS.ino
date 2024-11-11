#include <OneWire.h>
#include <DallasTemperature.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// Pin untuk DS18B20
#define ONE_WIRE_BUS 2
// Pin untuk laser
#define LASER_PIN 3

// Inisialisasi LCD (I2C address 0x27 dan ukuran 16x2)
LiquidCrystal_I2C lcd(0x27, 16, 2);

// Setup untuk komunikasi dengan DS18B20
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

void setup() {
  // Inisialisasi LCD
  lcd.begin(16,2);
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Temp: ");

  // Inisialisasi DS18B20
  sensors.begin();

  // Inisialisasi pin untuk laser
  pinMode(LASER_PIN, OUTPUT);
  digitalWrite(LASER_PIN, HIGH); // Laser akan selalu menyala

  // Serial monitor (opsional)
  Serial.begin(9600);
}

void loop() {
  // Meminta sensor untuk membaca suhu
  sensors.requestTemperatures();
  float temperatureC = sensors.getTempCByIndex(0);

  // Tampilkan suhu pada LCD
  lcd.setCursor(6, 1);
  lcd.print(temperatureC);
  lcd.print(" C  ");

  // Laser selalu menyala
  lcd.setCursor(0, 0);
  lcd.print("PENGUKUR SUHU");

  // Tampilkan suhu di Serial Monitor (opsional)
  Serial.print("Temp: ");
  Serial.print(temperatureC);
  Serial.println(" C");

  delay(1000); // Update setiap 1 detik
}
