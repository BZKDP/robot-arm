#include <SCServo.h>
SMS_STS st;
#define S_RXD 16
#define S_TXD 17

void setup() {
  Serial.begin(115200);
  Serial1.begin(1000000, SERIAL_8N1, S_RXD, S_TXD);
  st.pSerial = &Serial1;
  delay(600);
  Serial.println("=== ping oboih serv ===");
  st.EnableTorque(1, 0);
  st.EnableTorque(2, 0);
}

void loop() {
  int p1 = st.Ping(1);
  int p2 = st.Ping(2);
  int pos1 = st.ReadPos(1);
  int pos2 = st.ReadPos(2);
  Serial.print("ID1 ping="); Serial.print(p1); Serial.print(" pos="); Serial.print(pos1);
  Serial.print("   |   ID2 ping="); Serial.print(p2); Serial.print(" pos="); Serial.println(pos2);
  delay(400);
}
