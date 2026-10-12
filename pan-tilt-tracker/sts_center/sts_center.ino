#include <SCServo.h>
SMS_STS st;
#define S_RXD 16
#define S_TXD 17

void setup() {
  Serial.begin(115200);
  Serial1.begin(1000000, SERIAL_8N1, S_RXD, S_TXD);
  st.pSerial = &Serial1;
  delay(600);
  Serial.println("=== center oboih -> 2048 ===");
  st.EnableTorque(1, 1);
  st.EnableTorque(2, 1);
  st.WritePosEx(1, 2048, 1200, 50);
  st.WritePosEx(2, 2048, 1200, 50);
  delay(1500);
}

void loop() {
  Serial.print("ID1 pos="); Serial.print(st.ReadPos(1));
  Serial.print("   ID2 pos="); Serial.println(st.ReadPos(2));
  delay(500);
}
