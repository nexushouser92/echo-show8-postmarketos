# WiFi Monitor Mode on Amazon Echo Show 8 (2nd Gen) running postmarketOS

> **Device:** Amazon Echo Show 8 2nd Gen (codename `athena` / `kaeru`)  
> **SoC:** MediaTek MT8183 (8× Cortex-A53)  
> **OS:** postmarketOS (Alpine Linux, Phosh/GTK4)  
> **Kernel:** 6.18.56-techo5-athena  
> **WiFi chip:** MediaTek MT7921 (supports concurrent managed + monitor interfaces)

For full hardware compatibility details see **[hardware-compatibility.md](hardware-compatibility.md)**.

![Desktop running postmarketOS on Echo Show 8](screenshots/desktop.png)

This guide documents how to:
1. Access the device via USB serial console (no password needed)
2. Enable passwordless SSH over USB networking
3. Create a `mon0` monitor-mode interface without dropping the WiFi connection
4. Make monitor mode persistent across reboots
5. Fix the duplicate launcher UI (echo-launcher vs echo-taskbar)

---

## Prerequisites

### Hardware
- Amazon Echo Show 8 2nd Gen with postmarketOS already installed  
  (use the [saiyaku-athena](https://github.com/R0rt1z2/saiyaku) tool to flash it)
- USB-C cable

### Software (Windows host)
- Python 3.x
- pyserial: `pip install pyserial`
- OpenSSH client (built into Windows 10+)

### How the USB gadget works

postmarketOS creates a Linux USB composite gadget on the device with two interfaces:

| Interface | Windows driver | Function |
|-----------|---------------|----------|
| MI_00 — CDC-ACM | `usbser.sys` (built-in) | Serial console, auto-login as root on `ttyGS0` → **COM9** |
| MI_02 — CDC-ECM | CDC-ECM / RNDIS driver | USB network adapter: device `172.16.42.1`, host `172.16.42.2` |

The CDC-ACM serial port (COM9) works out of the box on Windows with no driver install.  
The CDC-ECM network interface needs a driver; install `usb_driver.inf` from the postmarketOS driver package.

---

## 1. USB Serial Access

The device exposes an auto-login root shell over the serial port. You can send commands to it from Windows using Python + pyserial.

### `serial_cmd.py` — run a single command

```python
import serial, sys, time, random, re

PORT = "COM9"
BAUD = 115200

cmd = sys.argv[1] if len(sys.argv) > 1 else "id"
wait = float(sys.argv[2]) if len(sys.argv) > 2 else 10

tag = str(random.randint(100000, 999999))
marker = ("DONE" + tag).encode()

ser = serial.Serial(PORT, BAUD, timeout=0.3)
time.sleep(0.5)
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
lines = s.splitlines()
print("\n".join(lines))
```

**Usage:**
```
python serial_cmd.py "uname -a"
python serial_cmd.py "ip addr show" 15
```

### `run_fix.py` — run a multi-line shell script

```python
import serial, sys, time, random, re

PORT = "COM9"
BAUD = 115200

with open(sys.argv[1], 'r') as f:
    script = f.read()

tag = str(random.randint(100000, 999999))
marker = ("DONE" + tag).encode()

ser = serial.Serial(PORT, BAUD, timeout=0.3)
time.sleep(0.5)
while ser.in_waiting:
    ser.read(ser.in_waiting)
    time.sleep(0.1)

cmd = "sh -s <<'SCRIPT'\n" + script + "\nSCRIPT\necho DO''NE" + tag + "\n"
ser.write(cmd.encode())

out = b""
t = time.time()
wait = float(sys.argv[2]) if len(sys.argv) > 2 else 30
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
print(s)
```

**Usage:**
```
python run_fix.py my_script.sh 30
```

---

## 2. Enable Passwordless SSH

postmarketOS ships OpenSSH with `PermitRootLogin prohibit-password` by default, which blocks login without a key even if the root password is empty.

### `fix_ssh.sh`

```sh
#!/bin/sh
passwd -d root
passwd -d kali 2>/dev/null || true
sed -i '/PermitRootLogin/d' /etc/ssh/sshd_config
sed -i '/PermitEmptyPasswords/d' /etc/ssh/sshd_config
echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
echo "PermitEmptyPasswords yes" >> /etc/ssh/sshd_config
grep -E "PermitRoot|PermitEmpty" /etc/ssh/sshd_config
rc-service sshd restart
echo "SSH_FIXED"
```

**Deploy via serial:**
```
python run_fix.py fix_ssh.sh 30
```

**Verify SSH works:**
```
ssh root@172.16.42.1
# or over WiFi:
ssh root@192.168.1.190
```

> **Why `sed -i '/PermitRootLogin/d'` instead of `sed -i 's/.../.../'`?**  
> Alpine's default `sshd_config` has the line commented out as `#PermitRootLogin prohibit-password`.  
> A simple substitution only matches the uncommented form. Deleting all matching lines first (commented or not) and then appending the desired value is the reliable approach.

---

## 3. WiFi Monitor Mode (without dropping the WiFi connection)

The MT7921 supports concurrent interface modes. You can add a virtual `mon0` monitor interface while `wlan0` stays connected to your AP.

### Verify concurrent mode support

```sh
iw phy phy0 info | grep -A10 "Supported interface modes"
```

Expected output includes both `managed` and `monitor`.

### Enable monitor mode (one-shot)

```sh
# Install iw if not present
apk add iw

# Create monitor interface (keeps wlan0 connected)
iw phy phy0 interface add mon0 type monitor
ip link set mon0 up

# Verify
iw dev mon0 info
```

Output:
```
Interface mon0
        ifindex 4
        wdev 0x2
        addr 00:0c:43:26:60:00
        type monitor
        wiphy 0
        txpower 20.00 dBm
```

---

## 4. Make Monitor Mode Persistent (OpenRC)

postmarketOS uses OpenRC. Scripts in `/etc/local.d/*.start` are executed at boot by the `local` service.

### `mon0_persist.sh`

```sh
#!/bin/sh
printf '#!/bin/sh\niw phy phy0 interface add mon0 type monitor 2>/dev/null || true\nip link set mon0 up\n' \
    > /etc/local.d/mon0.start
chmod 755 /etc/local.d/mon0.start
rc-update add local default
rc-service local start
iw dev mon0 info
echo PERSIST_OK
```

**Deploy:**
```
python run_fix.py mon0_persist.sh 20
```

**Verify after reboot:**
```sh
iw dev
# Should show both wlan0 (managed) and mon0 (monitor)
```

### Why this works

| Mechanism | Detail |
|-----------|--------|
| `/etc/local.d/mon0.start` | Executed by OpenRC `local` service at every boot |
| `2>/dev/null \|\| true` | Silently skips if `mon0` already exists (e.g., resumed from suspend) |
| `rc-update add local default` | Ensures `local` service is in the `default` runlevel |

---

## 5. Fix Duplicate Launcher UI

postmarketOS on the Echo Show 8 ships with two autostart entries that conflict:

| Entry | File | Function |
|-------|------|----------|
| `echo-launcher` | `/home/user/.config/autostart/echo-launcher.desktop` | Full home screen with app grid + search bar (basic desktop view) |
| `echo-taskbar` | `/home/user/.config/autostart/echo-taskbar.desktop` | Bottom bar that includes its own launcher popup — causes overlap |

**Remove echo-taskbar (keep echo-launcher):**
```sh
rm /home/user/.config/autostart/echo-taskbar.desktop
pkill -f echo-taskbar
```

**Verify:**
```sh
ls /home/user/.config/autostart/
# echo-launcher.desktop  echo-osk-dismiss.desktop

ps aux | grep echo-launcher | grep -v grep
# Should show echo-launcher running, no echo-taskbar
```

The device will show the basic desktop view (wallpaper + app icons + search bar) on next login.

---

## Workflow Summary

```
Echo Show 8 (postmarketOS)
        │
        │ USB-C
        │
   Windows host
        │
        ├─ COM9 (CDC-ACM serial) ──► serial_cmd.py / run_fix.py
        │                              Auto-login root shell
        │
        └─ 172.16.42.1 (CDC-ECM) ──► ssh root@172.16.42.1
                                       After SSH fix applied
```

**Step order:**
1. Plug in USB → COM9 appears automatically
2. Run `fix_ssh.sh` via serial to unlock SSH
3. Connect via SSH for interactive use
4. Run `mon0_persist.sh` to enable persistent monitor mode
5. Remove `echo-taskbar.desktop` to fix UI

---

## References

- [postmarketOS wiki — Amazon Echo Show 8 (2nd gen)](https://wiki.postmarketos.org/wiki/Amazon_Echo_Show_8_(2nd_gen))
- [saiyaku-athena flash tool](https://github.com/R0rt1z2/saiyaku)
- [Alpine Linux OpenRC docs](https://wiki.alpinelinux.org/wiki/OpenRC)
- [`iw` manual](https://wireless.wiki.kernel.org/en/users/documentation/iw)

---

## Notes

- The WiFi MAC address (`00:0c:43:26:60:00`) is shared between `wlan0` and `mon0` since they are virtual interfaces on the same physical radio.
- Tested on postmarketOS edge (November 2024 build), Alpine Linux 3.21, kernel 6.x.
- The `iw` package must be installed: `apk add iw`.
