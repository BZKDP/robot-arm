/*
  One joint stand: ESP32 + TMC2209 STEP/DIR + AS5600.

  Default wiring for ESP32 boards marked with Dxx labels:
    TMC2209 STEP -> D12  (GPIO12)
    TMC2209 DIR  -> D14  (GPIO14)
    Lerdge TMC2209 pin 1 is EN, but it may be unprinted on the PCB silkscreen.
    Tie EN to GND for standalone use. PIN_EN stays -1 because ESP32 does not control it.
    AS5600 SDA   -> D21  (GPIO21)
    AS5600 SCL   -> D22  (GPIO22)

  Motor power never goes through ESP32. Use a separate 12-24V PSU on TMC VM/GND.
*/

#include <Arduino.h>
#include <Wire.h>

static const uint8_t PIN_STEP = 12;
static const uint8_t PIN_DIR  = 14;
static const int8_t PIN_EN   = -1;
static const uint8_t PIN_SDA  = 21;
static const uint8_t PIN_SCL  = 22;

static const uint8_t AS5600_ADDR = 0x36;
static const uint8_t AS5600_REG_STATUS = 0x0B;
static const uint8_t AS5600_REG_RAW_ANGLE_H = 0x0C;

enum RunMode {
  MODE_IDLE = 0,
  MODE_JOG = 1,
  MODE_GOTO = 2
};

RunMode mode = MODE_IDLE;
bool motorEnabled = false;
bool streamEnabled = true;
bool dirInvert = false;

int zeroRaw = 0;
int lastRaw = -1;
uint8_t lastMag = 0;
bool as5600Ok = false;

float jogSps = 0.0f;
float targetDeg = 0.0f;
float currentSps = 0.0f;
float maxSps = 50000.0f;
float autoMaxSps = 5000.0f;
float accelSps2 = 12000.0f;
float gotoDeadbandDeg = 1.0f;

uint32_t lastStepUs = 0;
uint32_t lastSpeedUs = 0;
uint32_t lastTelemetryMs = 0;
uint32_t lastSensorMs = 0;

String modeName() {
  if (mode == MODE_JOG) return "JOG";
  if (mode == MODE_GOTO) return "GOTO";
  return "IDLE";
}

void setEnable(bool en) {
  motorEnabled = en;
  if (PIN_EN >= 0) {
    digitalWrite(PIN_EN, en ? LOW : HIGH);
  }
  if (!en) {
    mode = MODE_IDLE;
    currentSps = 0;
    jogSps = 0;
  }
}

bool readReg(uint8_t reg, uint8_t *value) {
  Wire.beginTransmission(AS5600_ADDR);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom((int)AS5600_ADDR, 1) != 1) return false;
  *value = Wire.read();
  return true;
}

bool readRawAngle(int *raw) {
  Wire.beginTransmission(AS5600_ADDR);
  Wire.write(AS5600_REG_RAW_ANGLE_H);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom((int)AS5600_ADDR, 2) != 2) return false;
  int hi = Wire.read();
  int lo = Wire.read();
  *raw = ((hi & 0x0F) << 8) | lo;
  return true;
}

float rawToDeg(int raw) {
  int shifted = (raw - zeroRaw) & 0x0FFF;
  return shifted * (360.0f / 4096.0f);
}

float angleDiff(float target, float current) {
  float d = target - current;
  while (d > 180.0f) d -= 360.0f;
  while (d < -180.0f) d += 360.0f;
  return d;
}

void updateSensor() {
  int raw = 0;
  as5600Ok = readRawAngle(&raw);
  if (as5600Ok) {
    lastRaw = raw;
    uint8_t st = 0;
    if (readReg(AS5600_REG_STATUS, &st)) {
      lastMag = st;
    }
  }
}

void stepOnce(int sign) {
  bool dir = sign >= 0;
  if (dirInvert) dir = !dir;
  digitalWrite(PIN_DIR, dir ? HIGH : LOW);
  digitalWrite(PIN_STEP, HIGH);
  delayMicroseconds(2);
  digitalWrite(PIN_STEP, LOW);
}

void updateStepper() {
  float desired = 0.0f;
  uint32_t now = micros();

  if (motorEnabled && mode == MODE_JOG) {
    desired = jogSps;
  } else if (motorEnabled && mode == MODE_GOTO && as5600Ok && lastRaw >= 0) {
    float deg = rawToDeg(lastRaw);
    float err = angleDiff(targetDeg, deg);
    if (fabs(err) <= gotoDeadbandDeg) {
      mode = MODE_IDLE;
      desired = 0.0f;
    } else {
      float speed = 80.0f + fabs(err) * 12.0f;
      if (speed > autoMaxSps) speed = autoMaxSps;
      desired = (err > 0.0f) ? speed : -speed;
    }
  }

  if (desired > maxSps) desired = maxSps;
  if (desired < -maxSps) desired = -maxSps;

  if (lastSpeedUs == 0) lastSpeedUs = now;
  float dt = (uint32_t)(now - lastSpeedUs) / 1000000.0f;
  lastSpeedUs = now;
  float maxDelta = accelSps2 * dt;
  float delta = desired - currentSps;
  if (delta > maxDelta) delta = maxDelta;
  if (delta < -maxDelta) delta = -maxDelta;
  currentSps += delta;
  if (fabs(desired) < 1.0f && fabs(currentSps) < 1.0f) currentSps = 0.0f;

  float absSps = fabs(currentSps);
  if (!motorEnabled || absSps < 1.0f) return;

  uint32_t period = (uint32_t)(1000000.0f / absSps);
  if (period < 20) period = 20;
  if ((uint32_t)(now - lastStepUs) >= period) {
    lastStepUs = now;
    stepOnce(currentSps >= 0.0f ? 1 : -1);
  }
}

void printState() {
  float deg = (as5600Ok && lastRaw >= 0) ? rawToDeg(lastRaw) : -1.0f;
  Serial.print("STATE ms=");
  Serial.print(millis());
  Serial.print(" ok=");
  Serial.print(as5600Ok ? 1 : 0);
  Serial.print(" raw=");
  Serial.print(lastRaw);
  Serial.print(" deg=");
  Serial.print(deg, 2);
  Serial.print(" mag=0x");
  if (lastMag < 16) Serial.print('0');
  Serial.print(lastMag, HEX);
  Serial.print(" zero=");
  Serial.print(zeroRaw);
  Serial.print(" mode=");
  Serial.print(modeName());
  Serial.print(" en=");
  Serial.print(motorEnabled ? 1 : 0);
  Serial.print(" sps=");
  Serial.print(currentSps, 1);
  Serial.print(" max=");
  Serial.print(maxSps, 0);
  Serial.print(" accel=");
  Serial.print(accelSps2, 0);
  Serial.print(" target=");
  Serial.print(targetDeg, 2);
  Serial.print(" inv=");
  Serial.print(dirInvert ? 1 : 0);
  Serial.println();
}

float argFloat(const String &line, float fallback) {
  int sp = line.indexOf(' ');
  if (sp < 0) return fallback;
  return line.substring(sp + 1).toFloat();
}

int argInt(const String &line, int fallback) {
  int sp = line.indexOf(' ');
  if (sp < 0) return fallback;
  return line.substring(sp + 1).toInt();
}

void scanI2c() {
  Serial.println("I2C_SCAN_BEGIN");
  for (uint8_t addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      Serial.print("I2C addr=0x");
      if (addr < 16) Serial.print('0');
      Serial.println(addr, HEX);
    }
  }
  Serial.println("I2C_SCAN_END");
}

void printHelp() {
  Serial.println("Commands:");
  Serial.println("  EN 1|0       enable/disable TMC2209 output");
  Serial.println("  JOG <sps>    run at signed steps/sec, example JOG 200 or JOG -200");
  Serial.println("  STOP         stop motion, keep driver enable state");
  Serial.println("  ZERO         set current AS5600 angle as zero");
  Serial.println("  GOTO <deg>   closed-loop move to 0..360 deg using AS5600");
  Serial.println("  INV 1|0      invert motor direction");
  Serial.println("  MAX <sps>    limit manual speed");
  Serial.println("  ACCEL <sps2> acceleration in steps/sec^2");
  Serial.println("  STREAM 1|0   telemetry on/off");
  Serial.println("  SCAN         I2C scan");
  Serial.println("  STATUS       print one telemetry line");
  Serial.println("Pins: STEP=D12 DIR=D14 EN=not_connected SDA=D21 SCL=D22 baud=115200");
}

void handleCommand(String line) {
  line.trim();
  if (line.length() == 0) return;

  String up = line;
  up.toUpperCase();

  if (up == "HELP" || up == "?") {
    printHelp();
  } else if (up.startsWith("EN ")) {
    setEnable(argInt(up, 0) != 0);
    printState();
  } else if (up.startsWith("JOG ")) {
    jogSps = argFloat(up, 0.0f);
    if (jogSps > maxSps) jogSps = maxSps;
    if (jogSps < -maxSps) jogSps = -maxSps;
    mode = MODE_JOG;
    printState();
  } else if (up == "STOP") {
    mode = MODE_IDLE;
    jogSps = 0.0f;
    currentSps = 0.0f;
    printState();
  } else if (up == "ZERO") {
    if (as5600Ok && lastRaw >= 0) zeroRaw = lastRaw;
    printState();
  } else if (up.startsWith("GOTO ")) {
    targetDeg = argFloat(up, 0.0f);
    while (targetDeg < 0.0f) targetDeg += 360.0f;
    while (targetDeg >= 360.0f) targetDeg -= 360.0f;
    mode = MODE_GOTO;
    printState();
  } else if (up.startsWith("INV ")) {
    dirInvert = argInt(up, 0) != 0;
    printState();
  } else if (up.startsWith("MAX ")) {
    maxSps = argFloat(up, maxSps);
    if (maxSps < 1.0f) maxSps = 1.0f;
    if (maxSps > 50000.0f) maxSps = 50000.0f;
    printState();
  } else if (up.startsWith("ACCEL ")) {
    accelSps2 = argFloat(up, accelSps2);
    if (accelSps2 < 100.0f) accelSps2 = 100.0f;
    if (accelSps2 > 200000.0f) accelSps2 = 200000.0f;
    printState();
  } else if (up.startsWith("STREAM ")) {
    streamEnabled = argInt(up, 1) != 0;
    printState();
  } else if (up == "SCAN") {
    scanI2c();
  } else if (up == "STATUS") {
    printState();
  } else {
    Serial.print("ERR unknown command: ");
    Serial.println(line);
  }
}

void setup() {
  pinMode(PIN_STEP, OUTPUT);
  pinMode(PIN_DIR, OUTPUT);
  if (PIN_EN >= 0) {
    pinMode(PIN_EN, OUTPUT);
  }
  digitalWrite(PIN_STEP, LOW);
  digitalWrite(PIN_DIR, LOW);
  if (PIN_EN >= 0) {
    digitalWrite(PIN_EN, HIGH);
  }

  Serial.begin(115200);
  Wire.begin(PIN_SDA, PIN_SCL);
  Wire.setClock(400000);

  delay(300);
  updateSensor();
  if (as5600Ok && lastRaw >= 0) zeroRaw = lastRaw;

  Serial.println();
  Serial.println("ONE_JOINT_STAND ready");
  printHelp();
  printState();
}

void loop() {
  updateStepper();

  if ((millis() - lastSensorMs) >= 20) {
    lastSensorMs = millis();
    updateSensor();
  }

  while (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    handleCommand(line);
  }

  if (streamEnabled && (millis() - lastTelemetryMs) >= 100) {
    lastTelemetryMs = millis();
    printState();
  }
}
