import serial, time
PORT="COM3"
for baud in [115200, 921600]:
    try:
        s=serial.Serial(PORT, baud, timeout=0.4)
    except Exception as e:
        print(baud,"OPEN FAIL", e); continue
    time.sleep(0.2); data=b""; t0=time.time()
    while time.time()-t0<3.0:
        data += s.read(8192)
    s.close()
    magic=data.find(b"\xAA\x55\xAA\x55")
    txt=bytes(b for b in data if 9<=b<=126)
    print("=== baud",baud,"bytes",len(data),"MAGIC@",magic)
    print("  text:", txt[:240])
    print("  hexhead:", data[:24].hex())
