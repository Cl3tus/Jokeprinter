# 🖨️ Jokeprinter

A Raspberry Pi powered thermal receipt printer that prints a random dad joke or IT joke every time you press a button. Supports online joke APIs with automatic offline fallback, startup beeps, and a print queue for rapid button pressing.

---

## 📸 Features

- Prints a random **dad joke** or **IT joke** on a thermal receipt printer
- Fetches live jokes from the internet (two different APIs)
- **Automatic offline fallback** with 475+ local jokes when no internet is available
- **Startup beep** so you know the device is ready
- **Print queue** — press the button up to 10 times rapidly and all jokes will print in order
- **Debounce** to prevent accidental double presses
- Runs as a **systemd service** — starts automatically on boot
- Easy configuration via flags at the top of the script

---

## 🛒 Hardware Required

| Part | Notes |
|---|---|
| Raspberry Pi | Any model with GPIO and USB |
| Thermal receipt printer | USB, ESC/POS compatible |
| Momentary push button | Any normally-open tactile switch |
| 2× jumper wires | Female-to-female |

---

## 🔌 Wiring

```
Raspberry Pi GPIO17 (Pin 11) ──── [Button] ──── GND (Pin 9)
```

No resistor needed — the Pi's internal pull-up resistor is used.

```
GPIO Pin Layout (relevant pins):

 3V3  (1) [ ] [ ] (2)  5V
 SDA  (3) [ ] [ ] (4)  5V
 SCL  (5) [ ] [ ] (6)  GND ◄── Button leg 2
GPIO4  (7) [ ] [ ] (8)  TX
  GND  (9) [ ] [ ] (10) RX
GPIO17(11) [ ] [ ] (12) GPIO18
           ▲
      Button leg 1
```

---

## 🖨️ Printer Setup

Connect your thermal printer via USB. Find its Vendor ID and Product ID:

```bash
lsusb
# Example output:
# Bus 001 Device 004: ID 4b43:3830 Caysn Thermal Printer
#                        ^^^^ ^^^^
#                        VID  PID
```

Find the USB endpoints:

```bash
python3 -c "
import usb.core
dev = usb.core.find(idVendor=0x4b43, idProduct=0x3830)
for cfg in dev:
    for intf in cfg:
        for ep in intf:
            print('Endpoint:', hex(ep.bEndpointAddress))
"
```

Update `VENDOR_ID`, `PRODUCT_ID`, `in_ep` and `out_ep` in `jokeprinter.py` if your printer differs from the defaults.

---

## 🔧 Installation

### 1. Install OS

Flash **Raspberry Pi OS Lite** using [Raspberry Pi Imager](https://www.raspberrypi.com/software/).

### 2. Install dependencies

```bash
sudo apt update
sudo apt install python3-pip python3-usb libusb-1.0-0
pip3 install python-escpos pyusb requests --break-system-packages
```

### 3. Add user to printer group

```bash
sudo usermod -aG lp $USER
```

Log out and back in, or run `newgrp lp`.

### 4. Clone the repo

```bash
git clone https://github.com/yourusername/Jokeprinter.git
cd Jokeprinter
```

### 5. Test the printer

```bash
sudo sh -c 'echo "Hello!" > /dev/usb/lp0'
```

### 6. Run in test mode

Set `TEST_MODE = True` in `jokeprinter.py`, then:

```bash
python3 jokeprinter.py
```

Press Enter to print a joke.

### 7. Install as a service

```bash
sudo cp jokeprinter.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable jokeprinter
sudo systemctl start jokeprinter
```

---

## ⚙️ Configuration

All options are at the top of `jokeprinter.py`:

| Flag | Default | Description |
|---|---|---|
| `TEST_MODE` | `False` | `True` = use Enter key instead of GPIO button |
| `OFFLINE_MODE` | `False` | `True` = always use local jokes, skip internet |
| `STARTUP_BEEP` | `True` | `False` = disable beeps on startup |
| `MAX_QUEUE` | `10` | Maximum number of queued jokes |
| `LINE_WIDTH` | `24` | Characters per line (adjust to your printer width) |
| `BUTTON_PIN` | `17` | GPIO pin number (BCM numbering) |

---

## 🌐 Joke Sources

**Online:**
- [icanhazdadjoke.com](https://icanhazdadjoke.com/) — Dad jokes API
- [v2.jokeapi.dev](https://v2.jokeapi.dev/) — Programming/IT jokes API

**Offline fallback:**
- `jokes_dad.txt` — 254 dad jokes
- `jokes_it.txt` — 221 IT/programming jokes

The printer automatically falls back to offline jokes if no internet connection is available.

---

## 🔄 Adding a Second WiFi Network

To use the printer in multiple locations, add extra networks with NetworkManager:

```bash
sudo nmcli connection add type wifi ssid "NetworkName" \
  wifi-sec.key-mgmt wpa-psk \
  wifi-sec.psk "password" \
  connection.autoconnect yes
```

Set priorities so your home network is preferred:

```bash
sudo nmcli connection modify "HomeNetwork" connection.autoconnect-priority 10
sudo nmcli connection modify "OtherNetwork" connection.autoconnect-priority 5
```

---

## 📋 Systemd Service

Check status:
```bash
sudo systemctl status jokeprinter
```

View live logs:
```bash
sudo journalctl -u jokeprinter -f
```

Restart after config changes:
```bash
sudo systemctl restart jokeprinter
```

---

## 📁 File Structure

```
Jokeprinter/
├── jokeprinter.py          # Main script
├── jokes_dad.txt           # Offline dad jokes database
├── jokes_it.txt            # Offline IT jokes database
├── jokeprinter.service     # Systemd service file
├── requirements.txt        # Python dependencies
├── LICENSE                 # MIT License
└── README.md               # This file
```

---

## 📜 License

MIT — see [LICENSE](LICENSE)
