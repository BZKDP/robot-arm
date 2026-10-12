#include <SCServo.h>
SMS_STS st;
#define S_RXD 16
#define S_TXD 17

void setup() {
  Serial.begin(115200);
  Serial1.begin(1000000, SERIAL_8N1, S_RXD, S_TXD);
  st.pSerial = &Serial1;
  delay(600);
  st.EnableTorque(1, 1);
  st.EnableTorque(2, 1);
  st.WritePosEx(1, 2048, 1000, 50);
  st.WritePosEx(2, 2048, 1000, 50);
  delay(1500);
  st.EnableTorque(1, 0);   // otpustit moment - servy svobodny
  st.EnableTorque(2, 0);
  Serial.println("=== servy v centre, moment otpushen (pauza) ===");
}

void loop() {}
