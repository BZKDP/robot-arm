# 5-axis robo-arm build list

Current proven bench setup:

- ESP32 -> TMC2209 by STEP/DIR.
- Lerdge TMC2209 pin 1 EN must be tied to GND unless we later wire EN to ESP32.
- TMC2209 -> NEMA17 motor works.
- 12 V motor supply with 470 uF 50 V capacitor across VM/GND works for one motor.
- AS5600 is detected on I2C address 0x36.

## Required for five joints, delta from current bench

Assumed already owned:

- 5x CM36 planetary gearbox 1:71.
- 1x NEMA17 test motor.
- 5x TMC2209 drivers with heatsinks.
- 5x AS5600 modules with magnets.
- 5x 470 uF 50 V electrolytic capacitors.
- ESP32 DevKit.
- Wires, labels, basic WAGO terminals.
- Current 12 V 3 A PSU for one-motor tests.

Buy next, in priority order:

1. 4x NEMA17 motors, 42 mm frame, 5 mm shaft, about 1.5-1.7 A, about 40 N.cm. Same type as the tested motor is fine. Short shaft is better; long shaft can be cut.
2. 1-2x TCA9548A I2C multiplexer modules. One is enough, second is spare.
3. 1x 24 V 10 A PSU, preferably enclosed or terminal-block style. Current 12 V 3 A is only for one motor.
4. 1x inline fuse holder and fuses around 10 A for first full-arm tests.
5. 1x large motor-power switch or emergency stop button rated for DC current.
6. 2x power distribution blocks or WAGO rails: one for +VM, one for GND. Need at least 6 ports each: PSU plus/minus and 5 TMC drivers.
7. 5-10x local 2-pin screw terminals or WAGO pairs near drivers for capacitor + VM/GND.
8. 8-10x 608ZZ bearings, size 8x22x7 mm. Buy extras.
9. 1x smooth steel shaft/linear rod, 8 mm diameter, 300-500 mm length, to cut into joint support axles. Alternative: smooth-shoulder M8 bolts.
10. M3 screw kit: M3x8, M3x10, M3x12, M3x16, M3 nuts/washers.
11. M4 screw kit: M4x10, M4x12, M4x16, M4 nuts/washers.
12. Heat-set threaded inserts for 3D prints, M3, preferably 4-5 mm length.
13. 5x output hubs/couplers for the CM36 output shaft, or print/clamp custom hubs after measuring shaft diameter and flat/key geometry.
14. Cable sleeving or spiral wrap for wires along the links.
15. Heatshrink if not enough is already on hand.

### Per joint, 5 total

- 1x NEMA17 stepper, 42 mm frame, 5 mm shaft, about 1.5-1.7 A, about 40 N.cm.
- 1x CM36 planetary gearbox, 1:71. Already owned.
- 1x TMC2209 driver.
- 1x heatsink on TMC2209.
- 1x 470 uF 50 V electrolytic capacitor across driver VM/GND. Already owned.
- 1x AS5600 module.
- 1x diametric magnet for AS5600.
- 1x output magnet holder and fixed AS5600 bracket.
- Motor connector or screw terminal, 4 wires per motor.
- Adapter plate from NEMA17/CM36 to joint bracket.
- Hub/coupler from gearbox output shaft to arm link.

### Shared electronics

- 1x ESP32 DevKit. Current ESP32 is enough for first 5-axis version.
- 1x TCA9548A I2C multiplexer for five AS5600 sensors with identical 0x36 address.
- 1x motor power supply, preferably 24 V 10 A. Minimum for gentle tests: 12 V 10 A.
- 1x DC-DC buck converter 12/24 V -> 5 V, 2-3 A, if ESP32 will not stay powered from USB.
- Optional but recommended: 1x 3.3 V regulator/distribution board for sensors and driver VIO.
- Common GND bus for ESP32, all TMC2209, all AS5600, TCA9548A, and power supply minus.
- VM/+ motor power bus and motor-power GND bus, rated for full current.
- Main switch and emergency stop in the motor-power line.
- Inline fuse, about 10 A for 12 V testing or sized to the final PSU/current.
- 40/60 mm fan for TMC2209 cooling if multiple motors hold torque for long periods.

### Wiring and small parts

- WAGO or screw terminal blocks with enough ports for +VM and GND distribution.
- Wire for motor power bus: about 0.75-1.0 mm2.
- Wire for individual motors: about 0.3-0.5 mm2.
- Thin signal wire for STEP/DIR/I2C/EN.
- Heatshrink, labels, cable ties, ferrules or crimp terminals.
- 10 kOhm resistors if EN will be controlled from ESP32 later.

### Mechanics

- 4-6x 608ZZ bearings for supported joints.
- 4-6x 8 mm shafts or smooth M8 bolts for opposite-side supports.
- Aluminum U-brackets/forks and arm beams.
- M3/M4 bolts, washers, lock nuts, thread locker.
- 3D printed adapter plates, output hubs, bearing pockets, AS5600/magnet mounts.

## Recommended build order

1. Finish one motor+CM36 fit: gearbox must sit flush by hand, not be pulled by screws.
2. Mount one AS5600 on gearbox output side and verify angle changes.
3. Build a 5-driver electronics board with power bus, capacitors, labels, and cooling.
4. Add joints one at a time: motor test, gearbox test, AS5600 test, then combined test.
5. Only after 2-3 reliable joints, write multi-axis firmware.

## Controller choice

Use one ESP32 for now. Do not use Arduino Uno/Nano for the main arm controller: they are 5 V logic, have fewer useful pins, and would need level shifting for 3.3 V sensors/driver logic. Arduino Mega can work, but ESP32 is still cleaner for this design.
