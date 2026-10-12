import serial, time
PORT="COM4"
s=serial.Serial(PORT,115200,timeout=1.0); time.sleep(1.9); s.reset_input_buffer()
for cmd in [b"P\n", b"V\n", b"F 1\n", b"F 2\n"]:
    s.reset_input_buffer(); s.write(cmd); time.sleep(0.25); t0=time.time(); got=""
    while time.time()-t0<1.2:
        ln=s.readline().decode(errors="replace").strip()
        if ln: got=ln; break
    print(cmd.decode().strip(), "->", got)
s.close()
