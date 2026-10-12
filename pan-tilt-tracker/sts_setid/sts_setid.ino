#include <SCServo.h>
SMS_STS st;
#define S_RXD 16
#define S_TXD 17

void setup() {
  Serial.begin(115200);
  Serial1.begin(1000000, SERIAL_8N1, S_RXD, S_TXD);
  st.pSerial = &Serial1;
  delay(600);
  Serial.println("=== ID change 1 -> 2 ===");
  Serial.print("ping ID1 (do) = "); Serial.println(st.Ping(1));
  Serial.print("ping ID2 (do) = "); Serial.println(st.Ping(2));
  delay(150);

  st.unLockEprom(1);
  st.writeByte(1, SMS_STS_ID, 2);   // reg 5 = ID -> 2
  st.LockEprom(2);                  // servo teper ID 2
  delay(400);

  Serial.println("--- posle ---");
  Serial.print("ping ID1 = "); Serial.println(st.Ping(1));     // ojidaem -1
  Serial.print("ping ID2 = "); Serial.println(st.Ping(2));     // ojidaem 2
  Serial.print("ReadPos(2) = "); Serial.println(st.ReadPos(2));
}

void loop() {}
