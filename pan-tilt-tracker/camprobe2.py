import serial, time
for baud in [115200, 921600]:
    s=serial.Serial("COM3", baud, timeout=0.3)
    s.setDTR(False); s.setRTS(True); time.sleep(0.25)   # EN low = reset
    s.setDTR(False); s.setRTS(False); time.sleep(0.1)   # release -> run
    s.reset_input_buffer()
    data=b""; t0=time.time()
    while time.time()-t0<3.5:
        data += s.read(8192)
    s.close()
    txt=bytes(b for b in data if 9<=b<=126)
    print("=== baud",baud,"bytes",len(data),"MAGIC@",data.find(b'\xAA\x55\xAA\x55'))
    print("  text:", txt[:300])
    print("  hex :", data[:48].hex())
