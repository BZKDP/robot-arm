// One-axis bench controller for ESP32 + TMC2209.
//
// Wiring:
//   GPIO25 (D25) -> STEP
//   GPIO26 (D26) -> DIR
//   3V3           -> VIO
//   GND           -> common GND
//
// Serial protocol at 115200 baud:
//   SPEED <20..2000>  - STEP pulses per second
//   LEFT / RIGHT      - start continuous motion
//   STOP              - stop immediately
//   PING              - keep-alive while moving
//   STATUS            - report current state
//
// Safety properties:
//   * no automatic movement after boot;
//   * STEP is LOW while stopped;
//   * motion stops if keep-alive is absent for 500 ms.

constexpr uint8_t STEP_PIN = 25;
constexpr uint8_t DIR_PIN = 26;

constexpr uint16_t MIN_SPEED_PPS = 20;
constexpr uint16_t MAX_SPEED_PPS = 2000;
constexpr uint16_t DEFAULT_SPEED_PPS = 80;
constexpr uint16_t STEP_HIGH_US = 4;
constexpr uint32_t WATCHDOG_MS = 500;
constexpr uint16_t ACCELERATION_PPS2 = 300;

enum class Motion : uint8_t { Stopped, Left, Right };

Motion motion = Motion::Stopped;
uint16_t targetSpeedPps = DEFAULT_SPEED_PPS;
uint16_t currentSpeedPps = 0;
uint32_t stepIntervalUs = 1000000UL / MIN_SPEED_PPS;
uint32_t nextStepUs = 0;
uint32_t lastKeepAliveMs = 0;
uint32_t lastRampMs = 0;

String inputLine;

const char* motionName() {
  switch (motion) {
    case Motion::Left: return "LEFT";
    case Motion::Right: return "RIGHT";
    default: return "STOPPED";
  }
}

void stopMotor(const char* reason) {
  motion = Motion::Stopped;
  currentSpeedPps = 0;
  digitalWrite(STEP_PIN, LOW);
  Serial.print("STOPPED ");
  Serial.println(reason);
}

void setSpeed(uint16_t requested) {
  targetSpeedPps = constrain(requested, MIN_SPEED_PPS, MAX_SPEED_PPS);
  Serial.print("OK SPEED ");
  Serial.println(targetSpeedPps);
}

void startMotor(Motion requestedMotion) {
  digitalWrite(STEP_PIN, LOW);
  digitalWrite(DIR_PIN, requestedMotion == Motion::Right ? HIGH : LOW);
  delayMicroseconds(20);

  motion = requestedMotion;
  currentSpeedPps = MIN_SPEED_PPS;
  stepIntervalUs = 1000000UL / currentSpeedPps;
  lastKeepAliveMs = millis();
  lastRampMs = lastKeepAliveMs;
  nextStepUs = micros() + stepIntervalUs;

  Serial.print("MOVING ");
  Serial.print(motionName());
  Serial.print(" ");
  Serial.print(targetSpeedPps);
  Serial.println(" PPS TARGET");
}

void printStatus() {
  Serial.print("STATUS ");
  Serial.print(motionName());
  Serial.print(" TARGET ");
  Serial.print(targetSpeedPps);
  Serial.print(" CURRENT ");
  Serial.println(currentSpeedPps);
}

void processCommand(String command) {
  command.trim();
  command.toUpperCase();

  if (command.startsWith("SPEED ")) {
    const long requested = command.substring(6).toInt();
    if (requested < MIN_SPEED_PPS || requested > MAX_SPEED_PPS) {
      Serial.println("ERR SPEED_RANGE_20_2000");
      return;
    }
    setSpeed(static_cast<uint16_t>(requested));
  } else if (command == "LEFT") {
    startMotor(Motion::Left);
  } else if (command == "RIGHT") {
    startMotor(Motion::Right);
  } else if (command == "STOP") {
    stopMotor("COMMAND");
  } else if (command == "PING") {
    lastKeepAliveMs = millis();
  } else if (command == "STATUS") {
    printStatus();
  } else if (command.length() > 0) {
    Serial.println("ERR UNKNOWN_COMMAND");
  }
}

void serviceSerial() {
  while (Serial.available()) {
    const char c = static_cast<char>(Serial.read());
    if (c == '\n' || c == '\r') {
      if (inputLine.length() > 0) {
        processCommand(inputLine);
        inputLine = "";
      }
    } else if (inputLine.length() < 80) {
      inputLine += c;
    } else {
      inputLine = "";
      Serial.println("ERR COMMAND_TOO_LONG");
    }
  }
}

void serviceMotor() {
  if (motion == Motion::Stopped) return;

  const uint32_t nowMs = millis();
  if (nowMs - lastKeepAliveMs > WATCHDOG_MS) {
    stopMotor("WATCHDOG");
    return;
  }

  const uint32_t rampElapsedMs = nowMs - lastRampMs;
  if (rampElapsedMs >= 10 && currentSpeedPps != targetSpeedPps) {
    uint32_t change = (static_cast<uint32_t>(ACCELERATION_PPS2) * rampElapsedMs) / 1000UL;
    if (change == 0) change = 1;

    if (currentSpeedPps < targetSpeedPps) {
      currentSpeedPps = static_cast<uint16_t>(
          min<uint32_t>(targetSpeedPps, static_cast<uint32_t>(currentSpeedPps) + change));
    } else {
      const uint32_t reduced = currentSpeedPps > change ? currentSpeedPps - change : MIN_SPEED_PPS;
      currentSpeedPps = static_cast<uint16_t>(max<uint32_t>(targetSpeedPps, reduced));
    }

    stepIntervalUs = 1000000UL / currentSpeedPps;
    lastRampMs = nowMs;
  }

  const uint32_t now = micros();
  if (static_cast<int32_t>(now - nextStepUs) < 0) return;

  digitalWrite(STEP_PIN, HIGH);
  delayMicroseconds(STEP_HIGH_US);
  digitalWrite(STEP_PIN, LOW);

  nextStepUs += stepIntervalUs;
  if (static_cast<int32_t>(now - nextStepUs) >= 0) {
    nextStepUs = now + stepIntervalUs;
  }
}

void setup() {
  digitalWrite(STEP_PIN, LOW);
  digitalWrite(DIR_PIN, LOW);
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);

  inputLine.reserve(96);
  Serial.begin(115200);
  delay(400);
  Serial.println("READY MOTOR1_SAFE_CONTROLLER");
  printStatus();
}

void loop() {
  serviceSerial();
  serviceMotor();
}
