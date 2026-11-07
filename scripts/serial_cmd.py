import serial, sys, time, random, re

PORT = "COM9"
BAUD = 115200

cmd = sys.argv[1] if len(sys.argv) > 1 else "id"
wait = float(sys.argv[2]) if len(sys.argv) > 2 else 10

tag = str(random.randint(100000, 999999))
marker = ("DONE" + tag).encode()

ser = serial.Serial(PORT, BAUD, timeout=0.3)
time.sleep(0.5)

# drain stale output
while ser.in_waiting:
    ser.read(ser.in_waiting)
    time.sleep(0.1)

payload = ("stty -echo 2>/dev/null; " + cmd + "; echo DO''NE" + tag + "\r\n").encode()
ser.write(payload)

out = b""
t = time.time()
while time.time() - t < wait:
    chunk = ser.read(256)
    if chunk:
        out += chunk
    if marker in out:
        break

ser.close()

s = out.decode(errors="replace")
s = re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", s)
s = re.sub(r"\r\n", "\n", s)
s = s.split("DONE" + tag)[0]
# strip echoed command line
lines = s.splitlines()
print("\n".join(lines))
