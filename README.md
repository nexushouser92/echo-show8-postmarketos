# postmarketOS on Amazon Echo Show 8 (2nd Gen)

> **Device:** Amazon Echo Show 8 2nd Gen · codename `athena` / `kaeru`  
> **SoC:** MediaTek MT8183 · **OS:** postmarketOS edge (Alpine Linux)  
> **Kernel:** 6.18.56-techo5-athena · **UI:** Phosh (Wayland/GTK4)

This repository documents the process of running postmarketOS on the Amazon Echo Show 8 2nd Generation, including setup guides, hardware compatibility status, and scripts to control the device from a Windows host over USB.

![Desktop running postmarketOS on Echo Show 8 2nd Gen](screenshots/desktop.png)

---

## Contents

| File | Description |
|------|-------------|
| [hardware-compatibility.md](hardware-compatibility.md) | What works, what doesn't, known issues |
| [monitor-mode-postmarketos-echo-show8.md](monitor-mode-postmarketos-echo-show8.md) | Full guide: USB serial access, SSH setup, WiFi monitor mode + persistence |
| [screenshots/](screenshots/) | Device screenshots |

---

## Quick Start

### Flash postmarketOS

Use the official [saiyaku-athena](https://github.com/R0rt1z2/saiyaku) tool to flash postmarketOS onto the device via MTK Meta mode.

### Connect via USB (Windows)

Plug the device in via USB-C. It exposes a composite USB gadget:

| Interface | Windows port | Function |
|-----------|-------------|----------|
| CDC-ACM serial | COM9 | Auto-login root shell at 115200 baud |
| CDC-ECM network | RNDIS adapter | USB network — device at `172.16.42.1` |

The serial port (COM9) works with the built-in Windows `usbser.sys` driver — no install needed.

### Run a command over serial (Python)

```python
# serial_cmd.py — requires: pip install pyserial
import serial, sys, time, random, re

ser = serial.Serial("COM9", 115200, timeout=0.3)
time.sleep(0.5)
while ser.in_waiting: ser.read(ser.in_waiting); time.sleep(0.1)

tag = str(random.randint(100000, 999999))
cmd = f"stty -echo 2>/dev/null; {sys.argv[1]}; echo DO''NE{tag}\r\n"
ser.write(cmd.encode())

out = b""
t = time.time()
while time.time() - t < 10:
    chunk = ser.read(256)
    if chunk: out += chunk
    if ("DONE" + tag).encode() in out: break
ser.close()

s = out.decode(errors="replace")
import re
s = re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", s)
print(s.split("DONE" + tag)[0])
```

```
python serial_cmd.py "uname -a"
```

### Enable SSH (passwordless root)

```sh
# Run once via serial
passwd -d root
sed -i '/PermitRootLogin/d' /etc/ssh/sshd_config
sed -i '/PermitEmptyPasswords/d' /etc/ssh/sshd_config
echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
echo "PermitEmptyPasswords yes" >> /etc/ssh/sshd_config
rc-service sshd restart
```

Then: `ssh root@172.16.42.1` (USB) or `ssh root@<device-wifi-ip>`

---

## WiFi Monitor Mode

The MT7921 supports running `wlan0` in managed mode (connected to your AP) and `mon0` in monitor mode **at the same time**.

```sh
apk add iw
iw phy phy0 interface add mon0 type monitor
ip link set mon0 up
iw dev  # shows both interfaces
```

### Make it persistent across reboots

```sh
printf '#!/bin/sh\niw phy phy0 interface add mon0 type monitor 2>/dev/null || true\nip link set mon0 up\n' \
    > /etc/local.d/mon0.start
chmod 755 /etc/local.d/mon0.start
rc-update add local default
```

---

## Hardware Status

| Component | Status |
|-----------|--------|
| Display (LCD + backlight) | ✅ Working |
| Touchscreen (FT5x06) | ✅ Working |
| WiFi managed | ✅ Working |
| WiFi monitor mode | ✅ Working |
| Bluetooth | ✅ Working |
| Audio playback | ✅ Working |
| Microphone | ⚠️ Present, not fully tested |
| Camera (rear + front) | ⚠️ ISP driver loaded, not tested |
| Ambient light sensor (TCS3400) | ✅ Working |
| Accelerometer / Gyro | ❌ Not found |
| Battery reporting | ❓ No sysfs entries |
| USB gadget (serial + network) | ✅ Working |

→ Full details: [hardware-compatibility.md](hardware-compatibility.md)

---

## Scripts in This Repo

| Script | Purpose |
|--------|---------|
| `serial_cmd.py` | Send a single shell command over USB serial (COM9) |
| `run_fix.py` | Send a multi-line `.sh` script over USB serial |
| `fix_ssh.sh` | Unlock passwordless root SSH on the device |
| `mon0_persist.sh` | Create persistent monitor mode via OpenRC |

---

## Related

- [postmarketOS wiki — Amazon Echo Show 8 (2nd gen)](https://wiki.postmarketos.org/wiki/Amazon_Echo_Show_8_(2nd_gen))
- [saiyaku-athena — flash tool](https://github.com/R0rt1z2/saiyaku)
- [postmarketOS official site](https://postmarketos.org/)
