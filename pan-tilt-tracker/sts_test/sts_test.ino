#include <SCServo.h>
SMS_STS st;
#define S_RXD 16
#define S_TXD 17

void setup() {
  Serial.begin(115200);
  Serial1.begin(1000000, SERIAL_8N1, S_RXD, S_TXD);
  st.pSerial = &Serial1;
  delay(500);
  st.EnableTorque(1, 0);     // момент выкл -> крутить рукой
  Serial.println("=== STS3215 test ===");
}

void loop() {
  int pos = st.ReadPos(1);
  if (pos != -1) {
    Serial.print("ID 1  pozic = ");
    Serial.println(pos);
  } else {
    Serial.println("net otveta - proveri 7.4V / obshaya zemlya / uzel Signal");
  }
  delay(300);
}
