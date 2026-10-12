/*
  Robotic arm J1/J2 motion controller v2

  Hardware:
    ESP32 DevKit + 2 x LERDGE TMC2209 in standalone STEP/DIR mode
    J1 STEP=GPIO25, DIR=GPIO26
    J2 STEP=GPIO32, DIR=GPIO33

  Important electrical assumptions:
    - VM is powered from the external 12 V supply.
    - VIO is connected to ESP32 3V3.
    - ESP32 GND, both driver GND pins and PSU minus are common.
    - ENN on each LERDGE module is tied to that driver's GND.
    - MS1/MS2 are left open: the module uses 1/8 STEP/DIR microsteps and
      the TMC2209 interpolates them internally to 1/256.

  FastAccelStepper uses ESP32 RMT hardware, so serial traffic and the GUI do
  not add jitter to STEP pulses. Normal STOP decelerates. ESTOP and watchdog
  stop as quickly as the queued hardware pulses permit.
*/

#include <Arduino.h>
#include <FastAccelStepper.h>
#include <TMCStepper.h>

constexpr uint8_t AXIS_COUNT = 2;
constexpr uint16_t MOTOR_FULL_STEPS = 200;
constexpr uint8_t MICROSTEPS = 8;
constexpr float GEAR_RATIO = 71.0f;
constexpr float PULSES_PER_OUTPUT_DEGREE =
    (MOTOR_FULL_STEPS * MICROSTEPS * GEAR_RATIO) / 360.0f;

constexpr uint32_t MIN_SPEED_PPS = 80;
// Measured mechanical/electrical ceiling of the assembled arm on 2026-08-29.
// Keep this in firmware as the final safety barrier: even a bad PC command
// cannot ask either axis to enter the observed 7500+ PPS loss-of-sync region.
constexpr uint32_t MAX_SPEED_PPS = 7258;
constexpr uint32_t MIN_ACCEL_PPS2 = 200;
constexpr uint32_t MAX_ACCEL_PPS2 = 100000;
constexpr uint32_t MAX_SMOOTH_STEPS = 2000;
constexpr uint32_t WATCHDOG_MS = 600;

// LERDGE splits the TMC2209 single-wire UART into host-labelled TX/RX pads.
// HardwareSerial::begin() takes RX first and TX second.
constexpr uint8_t LOWER_UART_RX_PIN = 16;
constexpr uint8_t LOWER_UART_TX_PIN = 17;
constexpr uint8_t UPPER_UART_RX_PIN = 18;
constexpr uint8_t UPPER_UART_TX_PIN = 19;
constexpr uint32_t TMC_UART_BAUD = 115200;
constexpr float TMC_R_SENSE = 0.11f;
constexpr uint8_t TMC_ADDRESS = 0b00;
constexpr uint8_t TMC2209_EXPECTED_VERSION = 0x21;
constexpr uint32_t TMC_NOMINAL_CLOCK_HZ = 12000000;
constexpr uint32_t DEFAULT_HYBRID_TRANSITION_PPS = 947;  // ~3 output deg/s

struct Axis {
  const char* name;
  uint8_t stepPin;
  uint8_t dirPin;
  FastAccelStepper* motor;
  uint32_t targetSpeedPps;
  uint32_t accelerationPps2;
  uint32_t smoothSteps;
  bool inverted;
  bool jogRequested;
  int8_t requestedDirection;
};

void printAxisStatus(uint8_t index);

// Conservative defaults. The PC panel can change them live.
Axis axes[AXIS_COUNT] = {
    {"LOWER_FIRST", 25, 26, nullptr, 3200, 6000, 300, false, false, 0},
    {"UPPER_NEW", 32, 33, nullptr, 2400, 4000, 400, false, false, 0},
};

FastAccelStepperEngine engine;

HardwareSerial lowerDriverSerial(2);
HardwareSerial upperDriverSerial(1);
TMC2209Stepper lowerDriverUart(&lowerDriverSerial, TMC_R_SENSE, TMC_ADDRESS);
TMC2209Stepper upperDriverUart(&upperDriverSerial, TMC_R_SENSE, TMC_ADDRESS);

enum class DriverMode : uint8_t {
  PASSIVE,
  STEALTH,
  HYBRID,
  SPREAD,
};

struct DriverUartDiagnostic {
  const char* name;
  TMC2209Stepper* driver;
  uint8_t rxPin;
  uint8_t txPin;
  DriverMode requestedMode;
  uint32_t transitionPps;
  uint32_t thresholdTstep;
  bool configurationVerified;
};

DriverUartDiagnostic uartDrivers[AXIS_COUNT] = {
    {"LOWER_FIRST", &lowerDriverUart, LOWER_UART_RX_PIN, LOWER_UART_TX_PIN,
     DriverMode::PASSIVE, DEFAULT_HYBRID_TRANSITION_PPS, 0, false},
    {"UPPER_NEW", &upperDriverUart, UPPER_UART_RX_PIN, UPPER_UART_TX_PIN,
     DriverMode::PASSIVE, DEFAULT_HYBRID_TRANSITION_PPS, 0, false},
};

char inputLine[128];
size_t inputLength = 0;
uint32_t lastHeartbeatMs = 0;
bool watchdogFault = false;

const char* driverModeName(DriverMode mode) {
  switch (mode) {
    case DriverMode::STEALTH: return "STEALTH";
    case DriverMode::HYBRID: return "HYBRID";
    case DriverMode::SPREAD: return "SPREAD";
    default: return "PASSIVE";
  }
}

uint8_t readTmcVersion(TMC2209Stepper& driver) {
  // A just-powered TMC may miss the first request. Retry reads only; this
  // diagnostic stage deliberately writes no configuration registers.
  for (uint8_t attempt = 0; attempt < 3; ++attempt) {
    const uint8_t version = driver.version();
    if (version == TMC2209_EXPECTED_VERSION) return version;
    delay(3);
  }
  return driver.version();
}

void printDriverUartStatus(uint8_t index) {
  DriverUartDiagnostic& item = uartDrivers[index];
  const uint8_t version = readTmcVersion(*item.driver);
  const bool online = version == TMC2209_EXPECTED_VERSION;

  Serial.print("TMC ");
  Serial.print(index + 1);
  Serial.print(" name=");
  Serial.print(item.name);
  Serial.print(" uart=");
  Serial.print(online ? "ONLINE" : "OFFLINE");
  Serial.print(" version=0x");
  if (version < 0x10) Serial.print('0');
  Serial.print(version, HEX);
  Serial.print(" rx_gpio=");
  Serial.print(item.rxPin);
  Serial.print(" tx_gpio=");
  Serial.println(item.txPin);
}

void printAllDriverUartStatus() {
  for (uint8_t i = 0; i < AXIS_COUNT; ++i) printDriverUartStatus(i);
}

void printDriverDetailedStatus(uint8_t index) {
  DriverUartDiagnostic& item = uartDrivers[index];
  const uint8_t version = readTmcVersion(*item.driver);
  if (version != TMC2209_EXPECTED_VERSION) {
    item.configurationVerified = false;
    Serial.print("TMCDETAIL ");
    Serial.print(index + 1);
    Serial.print(" name=");
    Serial.print(item.name);
    Serial.print(" uart=OFFLINE version=0x");
    if (version < 0x10) Serial.print('0');
    Serial.print(version, HEX);
    Serial.print(" requested_mode=");
    Serial.println(driverModeName(item.requestedMode));
    return;
  }

  // All registers below are read-only accesses from this firmware stage.
  const uint32_t ioin = item.driver->IOIN();
  const uint32_t gconf = item.driver->GCONF();
  const uint8_t gstat = item.driver->GSTAT();
  const uint8_t ifcnt = item.driver->IFCNT();
  const uint32_t chopconf = item.driver->CHOPCONF();
  const uint32_t drvStatus = item.driver->DRV_STATUS();
  const uint32_t pwmconf = item.driver->PWMCONF();
  const uint32_t pwmScale = item.driver->PWM_SCALE();
  const uint32_t pwmAuto = item.driver->PWM_AUTO();
  const uint32_t tstep = item.driver->TSTEP();
  const uint16_t sgResult = item.driver->SG_RESULT();
  int16_t pwmScaleAuto = static_cast<int16_t>((pwmScale >> 16) & 0x1FF);
  if (pwmScaleAuto & 0x100) pwmScaleAuto -= 0x200;

  Serial.print("TMCDETAIL ");
  Serial.print(index + 1);
  Serial.print(" name=");
  Serial.print(item.name);
  Serial.print(" uart=ONLINE");
  Serial.print(" version=0x");
  Serial.print(version, HEX);
  Serial.print(" ioin=0x");
  Serial.print(ioin, HEX);
  Serial.print(" gconf=0x");
  Serial.print(gconf, HEX);
  Serial.print(" gstat=0x");
  Serial.print(gstat, HEX);
  Serial.print(" ifcnt=");
  Serial.print(ifcnt);
  Serial.print(" chopconf=0x");
  Serial.print(chopconf, HEX);
  Serial.print(" drv_status=0x");
  Serial.print(drvStatus, HEX);
  Serial.print(" pwmconf=0x");
  Serial.print(pwmconf, HEX);
  Serial.print(" pwm_scale=0x");
  Serial.print(pwmScale, HEX);
  Serial.print(" pwm_auto=0x");
  Serial.print(pwmAuto, HEX);
  Serial.print(" tstep=");
  Serial.print(tstep);
  Serial.print(" sg_result=");
  Serial.print(sgResult);
  Serial.print(" requested_mode=");
  Serial.print(driverModeName(item.requestedMode));
  Serial.print(" transition_pps=");
  Serial.print(item.transitionPps);
  Serial.print(" threshold_tstep=");
  Serial.print(item.thresholdTstep);
  Serial.print(" config_verified=");
  Serial.print(item.configurationVerified ? 1 : 0);
  Serial.print(" pin_en=");
  Serial.print((ioin >> 0) & 1);
  Serial.print(" pin_ms1=");
  Serial.print((ioin >> 2) & 1);
  Serial.print(" pin_ms2=");
  Serial.print((ioin >> 3) & 1);
  Serial.print(" pin_spread=");
  Serial.print((ioin >> 8) & 1);
  Serial.print(" mode=");
  Serial.print((drvStatus >> 30) & 1 ? "STEALTH" : "SPREAD");
  Serial.print(" standstill=");
  Serial.print((drvStatus >> 31) & 1);
  Serial.print(" cs_actual=");
  Serial.print((drvStatus >> 16) & 0x1F);
  Serial.print(" pwm_scale_sum=");
  Serial.print(pwmScale & 0xFF);
  Serial.print(" pwm_scale_auto=");
  Serial.print(pwmScaleAuto);
  Serial.print(" toff=");
  Serial.print(chopconf & 0x0F);
  Serial.print(" mres_code=");
  Serial.print((chopconf >> 24) & 0x0F);
  Serial.print(" intpol=");
  Serial.print((chopconf >> 28) & 1);
  Serial.print(" analog_current=");
  Serial.print((gconf >> 0) & 1);
  Serial.print(" register_microsteps=");
  Serial.print((gconf >> 7) & 1);
  Serial.print(" pwm_autoscale=");
  Serial.print((pwmconf >> 18) & 1);
  Serial.print(" pwm_autograd=");
  Serial.print((pwmconf >> 19) & 1);
  Serial.print(" otpw=");
  Serial.print((drvStatus >> 0) & 1);
  Serial.print(" ot=");
  Serial.print((drvStatus >> 1) & 1);
  Serial.print(" t120=");
  Serial.print((drvStatus >> 8) & 1);
  Serial.print(" t143=");
  Serial.print((drvStatus >> 9) & 1);
  Serial.print(" t150=");
  Serial.print((drvStatus >> 10) & 1);
  Serial.print(" t157=");
  Serial.print((drvStatus >> 11) & 1);
  Serial.print(" short_a=");
  Serial.print(((drvStatus >> 2) & 1) | ((drvStatus >> 4) & 1));
  Serial.print(" short_b=");
  Serial.print(((drvStatus >> 3) & 1) | ((drvStatus >> 5) & 1));
  Serial.print(" open_a=");
  Serial.print((drvStatus >> 6) & 1);
  Serial.print(" open_b=");
  Serial.println((drvStatus >> 7) & 1);
}

void printAllDriverDetailedStatus() {
  for (uint8_t i = 0; i < AXIS_COUNT; ++i) printDriverDetailedStatus(i);
}

uint32_t transitionPpsToTstep(uint32_t transitionPps) {
  if (transitionPps < MIN_SPEED_PPS) transitionPps = MIN_SPEED_PPS;
  if (transitionPps > MAX_SPEED_PPS) transitionPps = MAX_SPEED_PPS;
  uint32_t value = (TMC_NOMINAL_CLOCK_HZ + transitionPps / 2) / transitionPps;
  if (value < 1) value = 1;
  if (value > 0xFFFFF) value = 0xFFFFF;
  return value;
}

bool configureDriverMode(uint8_t index, DriverMode mode,
                         uint32_t transitionPps) {
  if (index >= AXIS_COUNT) return false;
  Axis& axis = axes[index];
  DriverUartDiagnostic& item = uartDrivers[index];

  if (axis.motor && axis.motor->isRunning()) {
    Serial.print("ERR TMCMODE_AXIS_RUNNING axis=");
    Serial.println(index + 1);
    return false;
  }
  if (readTmcVersion(*item.driver) != TMC2209_EXPECTED_VERSION) {
    item.configurationVerified = false;
    Serial.print("ERR TMCMODE_UART_OFFLINE axis=");
    Serial.println(index + 1);
    return false;
  }

  if (transitionPps < MIN_SPEED_PPS) transitionPps = MIN_SPEED_PPS;
  if (transitionPps > MAX_SPEED_PPS) transitionPps = MAX_SPEED_PPS;
  const uint32_t thresholdTstep =
      mode == DriverMode::HYBRID ? transitionPpsToTstep(transitionPps) : 0;
  const uint8_t ifcntBefore = item.driver->IFCNT();

  // Preserve all unknown/current GCONF bits, but explicitly retain the two
  // hardware facts this arm relies on: analog VREF current and MS1/MS2
  // external microstep selection. UART power-down pin use is disabled.
  uint32_t gconf = item.driver->GCONF();
  gconf |= (1UL << 0);   // I_SCALE_ANALOG: keep physical VREF in control
  gconf &= ~(1UL << 1);  // external 0.11 ohm sense resistors
  gconf |= (1UL << 6);   // PDN_DISABLE: PDN pin becomes UART
  gconf &= ~(1UL << 7);  // MSTEP_REG_SELECT=0: keep MS1/MS2 = external 1/8
  gconf |= (1UL << 8);   // input STEP filtering
  if (mode == DriverMode::SPREAD) gconf |= (1UL << 2);
  else gconf &= ~(1UL << 2);

  item.driver->GCONF(gconf);
  item.driver->TPWMTHRS(thresholdTstep);

  const uint8_t ifcntAfter = item.driver->IFCNT();
  const uint32_t verifyGconf = item.driver->GCONF();
  const bool shouldSpread = mode == DriverMode::SPREAD;
  const bool verify =
      ((verifyGconf >> 0) & 1) == 1 &&
      ((verifyGconf >> 1) & 1) == 0 &&
      ((verifyGconf >> 2) & 1) == (shouldSpread ? 1UL : 0UL) &&
      ((verifyGconf >> 6) & 1) == 1 &&
      ((verifyGconf >> 7) & 1) == 0;

  item.requestedMode = mode;
  item.transitionPps = transitionPps;
  item.thresholdTstep = thresholdTstep;
  item.configurationVerified = verify;

  Serial.print(verify ? "OK TMCMODE" : "ERR TMCMODE_VERIFY");
  Serial.print(" axis=");
  Serial.print(index + 1);
  Serial.print(" requested=");
  Serial.print(driverModeName(mode));
  Serial.print(" transition_pps=");
  Serial.print(transitionPps);
  Serial.print(" threshold_tstep=");
  Serial.print(thresholdTstep);
  Serial.print(" ifcnt_before=");
  Serial.print(ifcntBefore);
  Serial.print(" ifcnt_after=");
  Serial.println(ifcntAfter);
  return verify;
}

void printTelemetry() {
  Serial.println("TELEMETRY START");
  for (uint8_t i = 0; i < AXIS_COUNT; ++i) printAxisStatus(i);
  printAllDriverDetailedStatus();
  Serial.println("TELEMETRY END");
}

Axis* getAxis(int oneBasedIndex) {
  if (oneBasedIndex < 1 || oneBasedIndex > AXIS_COUNT) return nullptr;
  return &axes[oneBasedIndex - 1];
}

uint32_t clampU32(long value, uint32_t minimum, uint32_t maximum) {
  if (value < static_cast<long>(minimum)) return minimum;
  if (value > static_cast<long>(maximum)) return maximum;
  return static_cast<uint32_t>(value);
}

void applyAxisSettings(Axis& axis) {
  if (!axis.motor) return;
  axis.motor->setSpeedInHz(axis.targetSpeedPps);
  axis.motor->setAcceleration(axis.accelerationPps2);
  // Jerk-limited start/stop: acceleration itself rises linearly over this
  // number of STEP pulses before reaching the configured acceleration.
  axis.motor->setLinearAcceleration(axis.smoothSteps);
  axis.motor->applySpeedAcceleration();
}

void printAxisStatus(uint8_t index) {
  Axis& axis = axes[index];
  int32_t position = 0;
  int32_t speedMilliHz = 0;
  bool running = false;
  bool stopping = false;

  if (axis.motor) {
    position = axis.motor->getCurrentPosition();
    speedMilliHz = axis.motor->getCurrentSpeedInMilliHz();
    running = axis.motor->isRunning();
    stopping = axis.motor->isStopping();
  }

  const float positionDeg = position / PULSES_PER_OUTPUT_DEGREE;
  const float currentPps = speedMilliHz / 1000.0f;
  const float outputDegS = currentPps / PULSES_PER_OUTPUT_DEGREE;

  Serial.print("AXIS ");
  Serial.print(index + 1);
  Serial.print(" name=");
  Serial.print(axis.name);
  Serial.print(" state=");
  if (!axis.motor) Serial.print("FAULT");
  else if (stopping) Serial.print("STOPPING");
  else if (running) Serial.print("RUNNING");
  else Serial.print("IDLE");
  Serial.print(" requested=");
  Serial.print(axis.jogRequested ? axis.requestedDirection : 0);
  Serial.print(" target_pps=");
  Serial.print(axis.targetSpeedPps);
  Serial.print(" current_pps=");
  Serial.print(currentPps, 1);
  Serial.print(" output_deg_s=");
  Serial.print(outputDegS, 2);
  Serial.print(" accel_pps2=");
  Serial.print(axis.accelerationPps2);
  Serial.print(" smooth_steps=");
  Serial.print(axis.smoothSteps);
  Serial.print(" position_steps=");
  Serial.print(position);
  Serial.print(" position_deg_rel=");
  Serial.print(positionDeg, 2);
  Serial.print(" inverted=");
  Serial.println(axis.inverted ? 1 : 0);
}

void printStatus() {
  Serial.print("STATUS watchdog=");
  Serial.print(watchdogFault ? 1 : 0);
  Serial.print(" max_speed_pps=");
  Serial.print(MAX_SPEED_PPS);
  Serial.print(" pulses_per_output_degree=");
  Serial.println(PULSES_PER_OUTPUT_DEGREE, 5);
  for (uint8_t i = 0; i < AXIS_COUNT; ++i) printAxisStatus(i);
  printAllDriverUartStatus();
  Serial.println("STATUS END");
}

void stopAxis(Axis& axis, bool emergency) {
  axis.jogRequested = false;
  axis.requestedDirection = 0;
  if (!axis.motor) return;
  if (emergency) axis.motor->forceStop();
  else axis.motor->stopMove();
}

void stopAll(bool emergency, const char* reason) {
  for (uint8_t i = 0; i < AXIS_COUNT; ++i) stopAxis(axes[i], emergency);
  Serial.print(emergency ? "ESTOP " : "STOPPED ");
  Serial.println(reason);
}

void startJog(Axis& axis, int direction) {
  if (!axis.motor) {
    Serial.println("ERR AXIS_NOT_INITIALIZED");
    return;
  }
  if (direction == 0) {
    stopAxis(axis, false);
    return;
  }

  applyAxisSettings(axis);
  const int logicalDirection = direction > 0 ? 1 : -1;
  const int physicalDirection = axis.inverted ? -logicalDirection : logicalDirection;
  const MoveResultCode result =
      physicalDirection > 0 ? axis.motor->runForward() : axis.motor->runBackward();

  if (result != MOVE_OK) {
    Serial.print("ERR MOVE_RESULT ");
    Serial.println(static_cast<int>(result));
    return;
  }

  axis.jogRequested = true;
  axis.requestedDirection = logicalDirection;
  watchdogFault = false;
  lastHeartbeatMs = millis();
  Serial.print("OK JOG ");
  Serial.print(static_cast<int>(&axis - axes) + 1);
  Serial.print(" ");
  Serial.println(logicalDirection);
}

void configureAxis(Axis& axis, long speed, long acceleration,
                   long smoothSteps, int inverted) {
  axis.targetSpeedPps = clampU32(speed, MIN_SPEED_PPS, MAX_SPEED_PPS);
  axis.accelerationPps2 = clampU32(acceleration, MIN_ACCEL_PPS2, MAX_ACCEL_PPS2);
  axis.smoothSteps = clampU32(smoothSteps, 0, MAX_SMOOTH_STEPS);
  axis.inverted = inverted != 0;
  applyAxisSettings(axis);
}

void printHelp() {
  Serial.println("ARM_CONTROLLER_V2 commands:");
  Serial.println("  CONFIG <axis> <speed_pps> <accel_pps2> <smooth_steps> <invert_0_or_1>");
  Serial.println("  JOG <axis> <-1|1>");
  Serial.println("  STOP <axis>       smooth deceleration");
  Serial.println("  STOP ALL          smooth deceleration");
  Serial.println("  ESTOP             fastest stop, no deceleration");
  Serial.println("  ZERO <axis>       zero relative step counter while idle");
  Serial.println("  PING              motion watchdog heartbeat");
  Serial.println("  STATUS");
  Serial.println("  UART              read-only TMC2209 communication test");
  Serial.println("  TMCDETAIL         read-only TMC2209 register snapshot");
  Serial.println("  TELEMETRY         axis state plus detailed TMC snapshot");
  Serial.println("  TMCMODE <axis> <STEALTH|HYBRID|SPREAD> <transition_pps>");
}

void processCommand(const char* rawCommand) {
  String command(rawCommand);
  command.trim();
  command.toUpperCase();
  if (command.length() == 0) return;

  if (command == "PING") {
    lastHeartbeatMs = millis();
    return;
  }
  if (command == "STATUS") {
    printStatus();
    return;
  }
  if (command == "UART") {
    printAllDriverUartStatus();
    return;
  }
  if (command == "TMCDETAIL") {
    printAllDriverDetailedStatus();
    return;
  }
  if (command == "TELEMETRY") {
    printTelemetry();
    return;
  }
  if (command == "HELP" || command == "?") {
    printHelp();
    return;
  }
  if (command == "ESTOP") {
    watchdogFault = false;
    stopAll(true, "COMMAND");
    return;
  }
  if (command == "STOP ALL") {
    stopAll(false, "ALL");
    return;
  }

  int axisIndex = 0;
  int direction = 0;
  long speed = 0;
  long acceleration = 0;
  long smoothSteps = 0;
  int inverted = 0;
  char tmcModeText[16] = {0};
  long transitionPps = DEFAULT_HYBRID_TRANSITION_PPS;

  const int tmcModeFields =
      sscanf(command.c_str(), "TMCMODE %d %15s %ld", &axisIndex,
             tmcModeText, &transitionPps);
  if (tmcModeFields >= 2) {
    if (axisIndex < 1 || axisIndex > AXIS_COUNT) {
      Serial.println("ERR AXIS_RANGE_1_2");
      return;
    }
    DriverMode mode;
    if (strcmp(tmcModeText, "STEALTH") == 0) mode = DriverMode::STEALTH;
    else if (strcmp(tmcModeText, "HYBRID") == 0) mode = DriverMode::HYBRID;
    else if (strcmp(tmcModeText, "SPREAD") == 0) mode = DriverMode::SPREAD;
    else {
      Serial.println("ERR TMCMODE_EXPECTED_STEALTH_HYBRID_SPREAD");
      return;
    }
    if (mode == DriverMode::HYBRID && tmcModeFields != 3) {
      Serial.println("ERR TMCMODE_HYBRID_NEEDS_TRANSITION_PPS");
      return;
    }
    configureDriverMode(axisIndex - 1, mode,
                        static_cast<uint32_t>(max(transitionPps, 0L)));
    return;
  }

  if (sscanf(command.c_str(), "CONFIG %d %ld %ld %ld %d", &axisIndex,
             &speed, &acceleration, &smoothSteps, &inverted) == 5) {
    Axis* axis = getAxis(axisIndex);
    if (!axis) {
      Serial.println("ERR AXIS_RANGE_1_2");
      return;
    }
    configureAxis(*axis, speed, acceleration, smoothSteps, inverted);
    Serial.print("OK CONFIG ");
    Serial.println(axisIndex);
    printAxisStatus(axisIndex - 1);
    return;
  }

  if (sscanf(command.c_str(), "JOG %d %d", &axisIndex, &direction) == 2) {
    Axis* axis = getAxis(axisIndex);
    if (!axis) {
      Serial.println("ERR AXIS_RANGE_1_2");
      return;
    }
    if (direction != -1 && direction != 1) {
      Serial.println("ERR DIRECTION_MUST_BE_MINUS1_OR_1");
      return;
    }
    startJog(*axis, direction);
    return;
  }

  if (sscanf(command.c_str(), "STOP %d", &axisIndex) == 1) {
    Axis* axis = getAxis(axisIndex);
    if (!axis) {
      Serial.println("ERR AXIS_RANGE_1_2");
      return;
    }
    stopAxis(*axis, false);
    Serial.print("OK STOP ");
    Serial.println(axisIndex);
    return;
  }

  if (sscanf(command.c_str(), "ZERO %d", &axisIndex) == 1) {
    Axis* axis = getAxis(axisIndex);
    if (!axis || !axis->motor) {
      Serial.println("ERR AXIS_RANGE_OR_INIT");
      return;
    }
    if (axis->motor->isRunning()) {
      Serial.println("ERR ZERO_WHILE_RUNNING");
      return;
    }
    axis->motor->setCurrentPosition(0);
    Serial.print("OK ZERO ");
    Serial.println(axisIndex);
    return;
  }

  Serial.println("ERR UNKNOWN_COMMAND");
}

void serviceSerial() {
  while (Serial.available() > 0) {
    const char c = static_cast<char>(Serial.read());
    if (c == '\n' || c == '\r') {
      if (inputLength > 0) {
        inputLine[inputLength] = '\0';
        processCommand(inputLine);
        inputLength = 0;
      }
    } else if (inputLength < sizeof(inputLine) - 1) {
      inputLine[inputLength++] = c;
    } else {
      inputLength = 0;
      Serial.println("ERR COMMAND_TOO_LONG");
    }
  }
}

void serviceWatchdog() {
  bool jogActive = false;
  for (uint8_t i = 0; i < AXIS_COUNT; ++i) {
    if (axes[i].jogRequested) {
      jogActive = true;
      break;
    }
  }

  if (jogActive && millis() - lastHeartbeatMs > WATCHDOG_MS) {
    watchdogFault = true;
    stopAll(true, "WATCHDOG");
  }
}

void setup() {
  Serial.begin(115200);

  // Separate UART per module means both LERDGE boards may keep address 0 and
  // their existing standalone MS1/MS2=1/8 configuration. Do not call
  // TMC2209Stepper::begin() in this read-only diagnostic stage: begin() sets
  // mstep_reg_select and would make the register override the physical pins.
  lowerDriverSerial.begin(TMC_UART_BAUD, SERIAL_8N1,
                          LOWER_UART_RX_PIN, LOWER_UART_TX_PIN);
  upperDriverSerial.begin(TMC_UART_BAUD, SERIAL_8N1,
                          UPPER_UART_RX_PIN, UPPER_UART_TX_PIN);

  // Keep motion generation away from Arduino loop()/serial work on core 1.
  engine.init(0);

  for (uint8_t i = 0; i < AXIS_COUNT; ++i) {
#ifdef SUPPORT_SELECT_DRIVER_TYPE
    axes[i].motor = engine.stepperConnectToPin(axes[i].stepPin, DRIVER_RMT);
#else
    axes[i].motor = engine.stepperConnectToPin(axes[i].stepPin);
#endif
    if (axes[i].motor) {
      // Give DIR a very conservative 2 us setup pause before the next STEP.
      // The TMC2209 datasheet requires only tens of nanoseconds.
      axes[i].motor->setDirectionPin(axes[i].dirPin, true, 2);
      applyAxisSettings(axes[i]);
    }
  }

  lastHeartbeatMs = millis();
  delay(400);
  Serial.println("READY ARM_CONTROLLER_V2 RMT J1=25/26 J2=32/33");
  Serial.println("INFO Apply 12V, wait at least 1 second, then start motion.");
  printStatus();
}

void loop() {
  serviceSerial();
  serviceWatchdog();
  delay(1);
}
