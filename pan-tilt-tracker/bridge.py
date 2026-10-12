#!/usr/bin/env python
# Helper: obschenie s sts_bridge po COM. Ispolzovanie:
#   python bridge.py P              -> tekuschie pozicii
#   python bridge.py V              -> napryazhenie
#   python bridge.py M 1 2048 1500  -> dvinut servo
#   python bridge.py B 2048 2048    -> oba (pan tilt)
#   python bridge.py T 1 0          -> torque off
#   python bridge.py F 1            -> diag
import sys, time, serial

PORT = "COM9"
BAUD = 115200

def main():
    cmd = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "P"
    s = serial.Serial(PORT, BAUD, timeout=1.0)
    time.sleep(1.8)  # perezhdat reset/banner posle otkrytiya porta
    s.reset_input_buffer()
    s.write((cmd + "\n").encode())
    want = cmd.strip()[0]  # ozhidaemyy prefiks otveta (P/V/M->OK/B->OK/T->OK/F)
    t0 = time.time()
    while time.time() - t0 < 2.0:
        line = s.readline().decode(errors="replace").strip()
        if not line or line == "BRIDGE READY":
            continue
        print(line)
        break
    s.close()

if __name__ == "__main__":
    main()
