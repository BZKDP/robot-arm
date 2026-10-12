// sts_bridge — USB-komandnyy most PK <-> STS3215 (pan ID1, tilt ID2)
// Protokol (stroki, \n):
//   M <id> <pos> [spd] [acc]   -> WritePosEx (dvizhenie)
//   B <pan> <tilt> [spd]       -> oba srazu (ID1=pan, ID2=tilt)
//   P                          -> "P <pos1> <pos2>" tekuschie pozicii
//   V                          -> "V <mV1> <mV2>" napryazhenie
//   T <id> <0|1>               -> torque off/on
//   F <id>                     -> "F <id> <pos> <mV> <load> <temp>" diag
// Otvet na M/B: "OK". Na oshibku chteniya: -1.
#include <SCServo.h>
SMS_STS st;
#define S_RXD 16
#define S_TXD 17

char buf[64];
int blen = 0;

// FIZICHESKIYE PREDELY NAKLONA (id2): vverh=1519, vniz=3138. Dalshe lomaetsya.
#define ID2_UP   1519
#define ID2_DOWN 3138
int clampPos(int id, int pos) {
  if (id == 2) { if (pos < ID2_UP) pos = ID2_UP; if (pos > ID2_DOWN) pos = ID2_DOWN; }
  return pos;
}

void handle(char *s) {
  char c = s[0];
  if (c == 'P') {
    Serial.print("P "); Serial.print(st.ReadPos(1));
    Serial.print(" ");  Serial.println(st.ReadPos(2));
  } else if (c == 'V') {
    Serial.print("V "); Serial.print(st.ReadVoltage(1)*100);
    Serial.print(" ");  Serial.println(st.ReadVoltage(2)*100);
  } else if (c == 'M') {
    int id=0,pos=2048,spd=1500,acc=30;   // acc=30 -> myagkaya trapeciya (plavnost)
    sscanf(s+1, "%d %d %d %d", &id,&pos,&spd,&acc);
    pos = clampPos(id, pos);
    st.EnableTorque(id,1);
    st.WritePosEx(id,pos,spd,acc);
    Serial.println("OK");
  } else if (c == 'B') {
    int p=2048,t=2048,spd=1500;
    sscanf(s+1, "%d %d %d", &p,&t,&spd);
    t = clampPos(2, t);
    st.EnableTorque(1,1); st.EnableTorque(2,1);
    st.WritePosEx(1,p,spd,50);
    st.WritePosEx(2,t,spd,50);
    Serial.println("OK");
  } else if (c == 'H') {
    int id=1; sscanf(s+1, "%d", &id);
    int p = st.ReadPos(id);
    if (p >= 0) { st.EnableTorque(id,1); st.WritePosEx(id, p, 600, 25); }  // myagkaya ostanovka (ne ryvkom)
    Serial.println("OK");
  } else if (c == 'T') {
    int id=0,en=1; sscanf(s+1, "%d %d", &id,&en);
    st.EnableTorque(id,en);
    Serial.println("OK");
  } else if (c == 'F') {
    int id=1; sscanf(s+1, "%d", &id);
    Serial.print("F "); Serial.print(id);
    Serial.print(" "); Serial.print(st.ReadPos(id));
    Serial.print(" "); Serial.print(st.ReadVoltage(id)*100);
    Serial.print(" "); Serial.print(st.ReadLoad(id));
    Serial.print(" "); Serial.println(st.ReadTemper(id));
  }
}

void setup() {
  Serial.begin(115200);
  Serial1.begin(1000000, SERIAL_8N1, S_RXD, S_TXD);
  st.pSerial = &Serial1;
  delay(500);
  Serial.println("BRIDGE READY");
}

void loop() {
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == '\n' || ch == '\r') {
      if (blen > 0) { buf[blen]=0; handle(buf); blen=0; }
    } else if (blen < 63) {
      buf[blen++] = ch;
    }
  }
}
