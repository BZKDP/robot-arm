#include <SCServo.h>
SMS_STS st;
#define S_RXD 16
#define S_TXD 17

void moveBoth(int p1, int p2) {
  st.WritePosEx(1, p1, 1800, 50);
  st.WritePosEx(2, p2, 1800, 50);
}

void setup() {
  Serial.begin(115200);
  Serial1.begin(1000000, SERIAL_8N1, S_RXD, S_TXD);
  st.pSerial = &Serial1;
  delay(600);
  st.EnableTorque(1, 1);
  st.EnableTorque(2, 1);
  Serial.println("=== DEMO oboih serv ===");
}

void loop() {
  // 1) sinhronno tuda-suda
  moveBoth(1200, 1200); Serial.println("oba -> 1200"); delay(1100);
  moveBoth(2900, 2900); Serial.println("oba -> 2900"); delay(1100);
  // 2) v protivofaze
  moveBoth(1200, 2900); Serial.println("pan<->tilt vroz"); delay(1100);
  moveBoth(2900, 1200); Serial.println("pan<->tilt vroz"); delay(1100);
  // 3) v centr
  moveBoth(2048, 2048); Serial.println("oba -> centr");
  Serial.print("pos1="); Serial.print(st.ReadPos(1));
  Serial.print(" pos2="); Serial.println(st.ReadPos(2));
  delay(1200);
}
