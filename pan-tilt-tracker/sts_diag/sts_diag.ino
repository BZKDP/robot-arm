#include <SCServo.h>
SMS_STS st;
#define S_RXD 16
#define S_TXD 17

void setup() {
  Serial.begin(115200);
  Serial1.begin(1000000, SERIAL_8N1, S_RXD, S_TXD);
  st.pSerial = &Serial1;
  delay(500);
  Serial.println("=== STS3215 diag (read fixed) ===");
  Serial.print("Voltage(0.1V) = "); Serial.println(st.ReadVoltage(1));
  Serial.print("Mode = ");          Serial.println(st.ReadMode(1));
  st.EnableTorque(1, 1);
}

void loop() {
  st.WritePosEx(1, 1024, 1500, 50);
  delay(1500);
  Serial.print("cmd 1024 -> pos="); Serial.print(st.ReadPos(1));
  Serial.print("  mov=");           Serial.print(st.ReadMove(1));
  Serial.print("  V=");             Serial.println(st.ReadVoltage(1));

  st.WritePosEx(1, 3072, 1500, 50);
  delay(1500);
  Serial.print("cmd 3072 -> pos="); Serial.print(st.ReadPos(1));
  Serial.print("  mov=");           Serial.print(st.ReadMove(1));
  Serial.print("  V=");             Serial.println(st.ReadVoltage(1));
}
