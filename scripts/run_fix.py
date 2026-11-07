import serial, sys, time, random, re

PORT = "COM9"
BAUD = 115200

# Read script from file and run it line by line
with open(sys.argv[1], 'r') as f:
    script = f.read()

tag = str(random.randint(100000, 999999))
marker = ("DONE" + tag).encode()

ser = serial.Serial(PORT, BAUD, timeout=0.3)
time.sleep(0.5)

# drain
while ser.in_waiting:
    ser.read(ser.in_waiting)
    time.sleep(0.1)

# Send the whole script as a here-doc style execution
cmd = "sh -s <<'SCRIPT'\n" + script + "\nSCRIPT\necho DO''NE" + tag + "\n"
ser.write(cmd.encode())

out = b""
t = time.time()
wait = float(sys.argv[2]) if len(sys.argv) > 2 else 30
while time.time() - t < wait:
    chunk = ser.read(256)
    if chunk:
        out += chunk
        t_last = time.time()
    if marker in out:
        break

ser.close()

s = out.decode(errors="replace")
s = re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", s)
s = re.sub(r"\r\n", "\n", s)
s = s.split("DONE" + tag)[0]
print(s)
