# Hardware Compatibility — Amazon Echo Show 8 (2nd Gen) on postmarketOS

> Tested on postmarketOS edge, kernel `6.18.56-techo5-athena`, November 2024.  
> Device codename: `athena` / `kaeru` — SoC: MediaTek MT8183 (4× Cortex-A53 + 4× Cortex-A53)

Legend: ✅ Working · ⚠️ Partial · ❌ Not working · ❓ Untested

---

## Summary Table

| Component | Status | Notes |
|-----------|--------|-------|
| Display (LCD) | ✅ | Backlight control via sysfs, Panfrost GPU, Wayland/Phosh |
| Touchscreen | ✅ | FocalTech FT5x06, `event1` |
| WiFi (managed) | ✅ | MediaTek MT7921, connects to AP via NetworkManager |
| WiFi (monitor mode) | ✅ | Concurrent with managed — `mon0` via `iw` |
| WiFi (AP mode) | ✅ | Supported by driver (confirmed via `iw phy info`) |
| Bluetooth | ✅ | `hci0` powered on, controller visible |
| Audio playback | ✅ | `mt8183_athena` ALSA card, `pcmC0D0p` |
| Microphone | ⚠️ | Capture devices present (`pcmC0D1c`, `pcmC0D2c`), not fully tested |
| Camera (rear) | ⚠️ | ISP driver loaded (`mtk-camsv-isp`, `/dev/video0`), libcamera not tested |
| Camera (front) | ⚠️ | ISP driver loaded, not separately identified yet |
| Ambient light sensor | ✅ | TCS3400 (IIO device `iio:device0`) |
| Accelerometer/Gyro | ❌ | No IIO device found |
| GPU (3D) | ✅ | MediaTek DRM + Panfrost, renders Phosh/GTK4 |
| USB (device mode) | ✅ | CDC-ACM serial + CDC-ECM network gadget |
| eMMC storage | ✅ | `/dev/mmcblk0`, `mmcblk0p23` userdata |
| Battery/charging | ❓ | No sysfs power_supply entries found; battery meter likely broken |
| Cellular modem | ❌ | N/A — device is WiFi-only, no modem hardware |
| Speaker | ✅ | Sound card present, playback works |

---

## Detail

### CPU
```
Architecture: ARMv8 (AArch64)
SoC: MediaTek MT8183
Cores: 8 × ARM Cortex-A53
  - 4 × A53 @ up to 2.0 GHz (big cluster)
  - 4 × A53 @ up to 1.5 GHz (LITTLE cluster)
CPU part: 0xd03 (Cortex-A53)
```

### Memory
```
RAM: 2 GB LPDDR4
Swap: 1 GB (zram)
Available at idle: ~470 MB
```

### Storage
```
eMMC internal flash
  /dev/root (rootfs):   3.0 GB — 81% used
  mmcblk0p23 (userdata): 3.4 GB — 99% used ⚠️ (almost full)
```
> **Note:** userdata partition is nearly full (48 MB free). Consider cleaning up before installing additional packages.

### Display
```
Type: LCD
Backlight: /sys/class/backlight/backlight-lcd0/brightness (0–1023)
Current brightness: 576
Compositor: Phosh (Wayland)
GPU: MediaTek DRM (Panfrost open-source driver)
```
Screenshot of the desktop:  
![Desktop](screenshots/desktop.png)

### Touchscreen
```
Driver: Generic FT5x06 (FocalTech)
I2C address: 0x38 on i2c-1 (11011000.i2c)
Input device: /dev/input/event1
```

### WiFi
```
Chip: MediaTek MT7921
Driver: mt7921e (or mt76)
Interfaces: wlan0 (managed) + mon0 (monitor) — concurrent
Bands: 2.4 GHz (tested), 5 GHz (supported)
Channel widths: up to 160 MHz / 80+80 MHz
Supported modes: IBSS, managed, AP, AP/VLAN, monitor
MAC: 00:0c:43:26:60:00
```

Both managed and monitor interfaces share the same MAC address (they are virtual interfaces on the same physical radio).

Screenshot of monitor mode active alongside WiFi connection:  


### Bluetooth
```
Controller: hci0
Address: 00:0C:43:26:60:01
Manufacturer ID: 0x0046
Firmware version: 9
Name: echo-show8
State: Powered on
```

### Cameras
```
/dev/video0 — mtk-camsv-isp  (ISP / image signal processor)
/dev/media0 — mtk-camsv-isp  (media controller)
/dev/video1 — mtk-jpeg-enc   (hardware JPEG encoder)
```
Camera capture has not been fully tested. The ISP driver is loaded but `libcamera` or `media-ctl` pipeline setup may be required for actual capture.

### Audio
```
Sound card: mt8183_athena (ALSA card 0)
  device 0: pcmC0D0p — Playback (speaker output)
  device 1: pcmC0D1c — Capture (microphone)
  device 2: pcmC0D2c — Capture (secondary mic / AEC reference)
```

### Sensors
```
/sys/bus/iio/devices/iio:device0: TCS3400 (ambient light + RGB color sensor)
```
Accelerometer and gyroscope: **not found** — no IIO devices registered for IMU.

### USB Gadget (device connected to host)
```
VID: 0x1D6B  PID: 0x0104  Serial: TECHO5
  MI_00: CDC-ACM  → COM9 on Windows (auto-login root shell at 115200 baud)
  MI_02: CDC-ECM  → USB network 172.16.42.1 (device) / 172.16.42.2 (host)
```

### Power / Battery
The device does not expose battery information through the standard Linux `power_supply` sysfs interface. Battery level, charging status, and voltage are **not available** through standard tools. This is a known gap in the postmarketOS port.

---

## Known Issues

| Issue | Workaround |
|-------|-----------|
| `userdata` partition 99% full | `apk cache clean`, remove unused packages |
| Battery status not exposed | No workaround currently |
| Camera capture untested | Needs `libcamera` pipeline configuration |
| Accelerometer/gyro not found | Driver may not be mainlined yet |
| `PermitRootLogin` default blocks passwordless SSH | See [monitor-mode guide](monitor-mode-postmarketos-echo-show8.md) §2 |
