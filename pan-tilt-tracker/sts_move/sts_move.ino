#include <SCServo.h>
SMS_STS st;
#define S_RXD 16
#define S_TXD 17

void setup() {
  Serial.begin(115200);
  Serial1.begin(1000000, SERIAL_8N1, S_RXD, S_TXD);
  st.pSerial = &Serial1;
  delay(500);
  st.EnableTorque(1, 1);          // momentum ON -> servo budet derzhat i dvigat
  Serial.println("=== STS3215 MOVE test ===");
}

void loop() {
  st.WritePosEx(1, 1024, 1500, 50);   // pozic 1024, skorost 1500, uskor 50
  Serial.println("-> 1024");
  delay(1600);
  Serial.print("pos = "); Serial.println(st.ReadPos(1));

  st.WritePosEx(1, 3072, 1500, 50);   // pozic 3072
  Serial.println("-> 3072");
  delay(1600);
  Serial.print("pos = "); Serial.println(st.ReadPos(1));
}
