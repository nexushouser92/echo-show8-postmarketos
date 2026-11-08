# Hardware Compatibility — Amazon Echo Show 8 (2nd Gen) on postmarketOS

> Tested on postmarketOS edge, kernel `6.18.56-techo5-athena`.  
> Device codename: `athena` / `kaeru` — SoC: MediaTek MT8183

Legend: ✅ Working · ⚠️ Partial · ❌ Not working · ❓ Untested

---

## Summary Table

| Component | Status | Notes |
|-----------|--------|-------|
| Display (LCD) | ✅ | Backlight control via sysfs, Panfrost GPU, Wayland/Phosh |
| Touchscreen | ✅ | FocalTech FT5x06, `event1` |
| WiFi (managed) | ✅ | MediaTek MT7921, connects to AP via NetworkManager |
| WiFi (monitor mode) | ✅ | Concurrent with managed — `mon0` via `iw` |
| WiFi (AP mode) | ✅ | Supported by driver |
| Bluetooth | ✅ | `hci0` powered on, controller visible |
| Audio playback | ✅ | `mt8183_athena` ALSA card, `pcmC0D0p` |
| Microphone | ⚠️ | Capture devices present, not fully tested |
| Camera (rear) | ⚠️ | ISP driver loaded (`mtk-camsv-isp`, `/dev/video0`), libcamera not tested |
| Camera (front) | ⚠️ | ISP driver loaded, not separately identified yet |
| Ambient light sensor | ✅ | TCS3400 (IIO device `iio:device0`) |
| Accelerometer/Gyro | ❌ | No IIO device found |
| GPU (3D) | ✅ | MediaTek DRM + Panfrost, renders Phosh/GTK4 |
| USB (device mode) | ✅ | CDC-ACM serial + CDC-ECM network gadget |
| eMMC storage | ✅ | `/dev/mmcblk0`, `mmcblk0p23` userdata |
| Battery/charging | ❓ | No sysfs power_supply entries found |
| Cellular modem | ❌ | N/A — device is WiFi-only |
| Speaker | ✅ | Sound card present, playback works |

---

## Detail

### CPU & Memory
- **SoC:** MediaTek MT8183 (8 × ARM Cortex-A53)
- **RAM:** 2 GB LPDDR4 (Swap: 1 GB zram)

### Storage
- **Internal Flash:** eMMC (`/dev/root` and `mmcblk0p23` userdata)
- *Note:* Monitor the `userdata` partition for available capacity when installing packages.

### Display & Touch
- **Display:** LCD with sysfs backlight control and Panfrost GPU acceleration.
- **Touchscreen:** FocalTech FT5x06 (`/dev/input/event1`).

### Connectivity & Audio
- **WiFi:** MediaTek MT7921 supporting concurrent managed and monitor interfaces.
- **Bluetooth:** `hci0` controller active.
- **Audio:** `mt8183_athena` card with ALSA playback and capture device nodes.

### Sensors & USB
- **Sensors:** TCS3400 ambient light sensor active; IMU components not detected.
- **USB Gadget:** Exposes CDC-ACM serial console and CDC-ECM network interface.
- **Power:** Battery status reporting via standard sysfs entries is not available.

---

## Known Issues

| Issue | Workaround |
|-------|------------|
| `userdata` partition capacity | Clean package cache (`apk cache clean`) if space runs low |
| Battery status not exposed | No workaround currently |
| Camera capture untested | Requires `libcamera` pipeline configuration |
| Accelerometer/gyro not found | Driver pending mainline support |
