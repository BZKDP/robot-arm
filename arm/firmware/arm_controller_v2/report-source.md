# Research source report — J1/J2 motion control

Date: 2026-08-29  
Scope: ESP32 DevKit, two LERDGE TMC2209 modules, 17HS4401/17HS8401S motors, 12 V, CM36 1:71 gearboxes.

This is the canonical engineering research note behind `arm_controller_v2.ino` and `arm_control_panel.py`.

## Confirmed local hardware facts

- J1: STEP GPIO25, DIR GPIO26.
- J2: STEP GPIO32, DIR GPIO33.
- LERDGE ENN has a board pull-up; tying it to GND enables the driver.
- LERDGE standalone MS1/MS2 low/low selects 1/8 external microstepping; TMC interpolation remains enabled.
- LERDGE documentation states 4.75–28 V, 1.4 A RMS continuous, 1.77 A RMS short-term, Rsense 0.11 Ω, and `IRMS ≈ 0.88 × VREF`.
- Measured VREF 1.293 V therefore implies about 1.14 A RMS.
- The actually working J1 cable has coil pairs black+blue and red+green. A spare cable had different color pairing, so colors cannot be generalized.
- Both current joints use CM36 1:71 gearboxes.

Local evidence:

- `../motor1_safe_test/LERDGE_TMC2209.pdf`
- `../../wiring_v2/03_step_dir.svg`
- `../../base_j1/arm_v8_5axis.html`
- `../../PROJECT_AUDIT_2026-08-28.md`

## Derived kinematics

Assumptions: 1.8° motor = 200 fullsteps/rev, standalone 1/8 microstep, 71:1 reduction.

```text
motor STEP pulses/rev = 200 × 8 = 1600
output STEP pulses/rev = 1600 × 71 = 113600
STEP pulses/output degree = 113600 / 360 = 315.5556
output deg/s = STEP pulses/s / 315.5556
```

The old 2000 pulse/s ceiling was only 6.34°/s at the output. A useful 30°/s would need about 9467 pulse/s. Empirical testing of the assembled 12 V arm on 2026-08-29 found 7258 pulse/s stable (about 23.0°/s output and 272 motor RPM), while approximately 7500 pulse/s produced a sustained squeal and loss of synchronism. The current software therefore hard-limits both axes to 7258 pulse/s and recommends 6311 pulse/s (20°/s) for working margin.

## Driver findings

### STEP/DIR timing

The TMC2209 accepts rising STEP edges and lists typical minimum STEP high and low times of 100 ns, with only 20 ns DIR setup/hold requirements. Software-generated GPIO pulses were electrically long enough, but their timing depended on the Arduino loop and serial work. Hardware queued pulses remove that jitter source.

Primary source: [TMC2209 datasheet, STEP/DIR interface](https://www.analog.com/media/en/technical-documentation/data-sheets/tmc2209_datasheet_rev1.09.pdf).

### StealthChop automatic tuning

StealthChop2 requires:

1. a powered standstill phase, up to about 130 ms;
2. a constant medium-speed motion phase, typically 60–300 motor RPM and potentially up to 400 fullsteps.

The supply voltage or VREF should not be changed after tuning without repeating the process. The operating procedure therefore waits at least one second after applying VM before motion and tests a sustained medium-speed move before high-speed trials.

Primary sources: [TMC2209 datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/tmc2209_datasheet_rev1.09.pdf), [AN-015 StealthChop performance](https://www.analog.com/en/resources/app-notes/an-015.html).

### StealthChop versus SpreadCycle

- StealthChop is the best low/medium-speed acoustic mode and can damp some motor vibration.
- Its automatic voltage regulation has less high-acceleration and high-speed margin.
- SpreadCycle is current-controlled and better suited to high dynamics and high velocity.
- The ideal final driver configuration is velocity-based hybrid switching: StealthChop at low speed, SpreadCycle above a low transition threshold.
- Mode switching at excessive velocity can itself create a current/load-angle jerk and stall, so the threshold must be tuned on the actual arm.

The present board is wired only for STEP/DIR and fixed standalone settings. Firmware cannot enable UART hybrid mode without a physical UART connection and per-driver address strategy. Therefore v2 improves pulse generation and motion profiles now, while UART remains a documented phase-2 hardware change.

Primary sources: [AN-015](https://www.analog.com/en/resources/app-notes/an-015.html), [TMC2209 product page](https://www.analog.com/en/products/TMC2209.html), [TMCStepper official repository](https://github.com/teemuatlut/TMCStepper).

### Voltage, speed and torque

At increasing velocity, motor back EMF subtracts from the voltage available to build coil current. The current and torque therefore fall at speed; a higher STEP rate cannot manufacture missing electrical torque. The current setting is also below the motors' advertised 1.5 A rating, so the present setup intentionally leaves torque reserve unused.

Primary sources: [TMC2209 datasheet, PWM/back-EMF discussion](https://www.analog.com/media/en/technical-documentation/data-sheets/tmc2209_datasheet_rev1.09.pdf), [Analog Devices low-voltage motor control article](https://www.analog.com/en/resources/technical-articles/low-voltage-motor-control.html).

## Motion software comparison

| Candidate | Strength | Limitation here | Decision |
|---|---|---|---|
| Handwritten `micros()` loop | Small and easy to inspect | Serial/I2C/GUI workload causes pulse jitter; weak high-rate behavior | Replaced |
| AccelStepper | Familiar Arduino API | Software scheduling and lower high-speed headroom | Not selected |
| FastAccelStepper | ESP32 RMT/MCPWM hardware engines, 200 kstep/s class, per-axis queues, acceleration, linear acceleration ramp | Its built-in independent ramps are not a complete multi-axis Cartesian planner | Selected for J1/J2 jogging and low-level execution |
| FluidNC | Mature ESP32 CNC stack, RMT, configuration, web UI | CNC/G-code architecture is excessive for the current custom arm and future encoder control | Used as architectural evidence, not embedded wholesale |
| Klipper/Marlin | Mature trapezoid/look-ahead and resonance concepts | Designed around printer kinematics and much larger host/planner stacks | Algorithms studied; not transplanted wholesale |

Primary sources:

- [FastAccelStepper repository](https://github.com/gin66/FastAccelStepper)
- [FastAccelStepper API](https://github.com/gin66/FastAccelStepper/blob/master/extras/doc/FastAccelStepper_API.md)
- [Espressif Arduino RMT documentation](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/rmt.html)
- [FluidNC repository](https://github.com/bdring/FluidNC)
- [Klipper kinematics](https://github.com/Klipper3d/klipper/blob/master/docs/Kinematics.md)
- [Klipper resonance compensation](https://www.klipper3d.org/Resonance_Compensation.html)
- [Marlin firmware](https://github.com/MarlinFirmware/Marlin)

## Selected motion profile

`FastAccelStepper 1.2.7` is installed locally. Each axis receives a dedicated RMT engine. The library's `setLinearAcceleration()` ramps acceleration itself from zero over a configurable number of STEP pulses, producing a jerk-limited start/end region around the normal constant-acceleration ramp.

This is preferable to jumping instantly from zero acceleration to a high fixed acceleration. It also avoids attempting full input shaping before the arm has sensors: a serial robot's resonance changes with pose, payload, joint direction and backlash. Fixed input-shaper values measured in one pose may be wrong in another. AS5600 feedback and/or an accelerometer can support that later.

## Safety model implemented

- No motion at boot.
- Hold-to-jog UI.
- Smooth button-release stop.
- Separate immediate ESTOP.
- 600 ms motion heartbeat watchdog in ESP32.
- Independent axis limits in firmware: 80–7258 pulse/s and 200–100000 pulse/s². The speed ceiling is duplicated in the GUI and ESP32 firmware.
- No false absolute angle claim: the displayed position is explicitly relative STEP count until encoders/homing are installed.
- No automatic high-speed sweep without sensors/endstops.

## Remaining evidence gaps

| Gap | Why it matters | Resolution |
|---|---|---|
| Stable speed in every arm pose and payload | 7258 pulse/s was the best observed ceiling, but load varies with pose | Use 6311 pulse/s as the working profile; repeat loaded tests after encoders/end limits are installed |
| Driver heatsink temperature at sustained load | VREF and duty-cycle safety | Measure after 2, 5 and 10 minutes |
| Exact second cable pairing | Prevents cross-coil vibration | Continuity-test that cable independently |
| UART pad accessibility/address wiring on these exact boards | Needed for hybrid mode and diagnostics | Inspect board/pads and implement separate wiring revision |
| Absolute joint position and limits | Required for autonomous motion | Install AS5600/index/limit strategy before GOTO/IK |
| Regenerative supply rise during heavy deceleration | Can stress VM rail | Measure VM peaks; add suitable clamp/TVS if needed |

## Decision

The immediate speed problem is mostly a units/architecture problem: 1:71 demands far more STEP pulses than the original 2000 pulse/s ceiling, and a polling loop is the wrong generator. The v2 hardware-RMT controller is the correct next test layer. The eventual high-performance controller should add UART driver diagnostics/hybrid chopper control and actual joint feedback, not hide those missing wires and sensors behind more elaborate open-loop code.
