# Wireless and Future Upgrades

Version 1 (this repository) works over a USB cable. Everything below is an upgrade path. Nothing on this page is needed to use version 1.

- Wireless with same functionality
- Esp32 can act as a independent keyboard
- Enable and disable the program anytime

## Why wireless is easy here

The ESP32 only sends short text messages (`1`, `2`, `H`, `R`). In the code this happens in exactly one place on each side:

| Side | The one place that changes for wireless |
|---|---|
| ESP32 | The function `send(String m)` |
| Laptop | The function `messages()` |

The click logic, the `ACTIONS` table and every action stay exactly the same.

## Ways to go wireless

| Way | Good | Not so good |
|---|---|---|
| **Wi-Fi (UDP messages)** | Keeps every action. Easy. Fast | ESP32 and laptop must be on the same **2.4 GHz** Wi-Fi |
| Bluetooth keyboard (the ESP32 pretends to be a keyboard, for example with an ESP32 BLE keyboard library) | No Python at all. Pairs like a normal keyboard | Only key presses. No opening apps, sleep, shutdown scripts |
| Bluetooth Low Energy to Python (`bleak` library) | No Wi-Fi needed. Keeps every action | More code. Pairing can be fiddly |

The rest of this section builds the Wi-Fi version. In both cases the ESP32 still needs power, so plug it into a power bank or a phone charger (a power-only USB connection is enough, no data needed).

## Wi-Fi version, step by step

Important facts first:

- The ESP32 only supports **2.4 GHz** Wi-Fi, not 5 GHz. Many phones can create a 2.4 GHz hotspot. On Android look for the hotspot setting "AP band" and pick 2.4 GHz. On iPhone turn on "Maximize Compatibility" in Personal Hotspot.
- Use WPA2 security, not WPA3.
- Public or school Wi-Fi often blocks devices from talking to each other. If nothing arrives, use a phone hotspot or a home router.

### Part 1. New ESP32 code

Same button logic as version 1, plus Wi-Fi. Edit the three lines at the top, then upload as usual.

```cpp
#include <WiFi.h>
#include <WiFiUdp.h>

const char* SSID = "YOUR_2.4GHZ_WIFI_NAME";
const char* PASS = "YOUR_WIFI_PASSWORD";
const char* SECRET = "change-me";
const int PORT = 4210;

const int PIN = 4;

const unsigned long DEBOUNCE = 25;
const unsigned long GAP = 300;
const unsigned long HOLD = 1500;

int last = HIGH;
int count = 0;
int held = 0;

unsigned long t = 0;
unsigned long tPress = 0;
unsigned long tRelease = 0;

WiFiUDP udp;

void send(String m) {
  Serial.println(m);
  for (int i = 0; i < 2; i++) {
    udp.beginPacket(IPAddress(255, 255, 255, 255), PORT);
    udp.print(String(SECRET) + ":" + m);
    udp.endPacket();
    delay(5);
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN, INPUT_PULLUP);
  WiFi.begin(SSID, PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(200);
  }
  WiFi.setSleep(false);
  Serial.println(WiFi.localIP());
}

void loop() {
  int r = digitalRead(PIN);
  unsigned long now = millis();

  if (r != last && now - t > DEBOUNCE) {
    t = now;
    last = r;

    if (r == LOW) {
      tPress = now;
    } else if (held) {
      send("R");
      held = 0;
    } else {
      count++;
      tRelease = now;
    }
  }

  if (last == LOW && !held && now - tPress > HOLD) {
    held = 1;
    count = 0;
    send("H");
  }

  if (count && last == HIGH && now - tRelease > GAP) {
    send(String(count));
    count = 0;
  }
}
```

What is different: the `send` function now also broadcasts each message over Wi-Fi, twice (a lost message could leave Alt stuck, so the second copy is a safety net). `SECRET` is a password-like word that the laptop checks.

### Part 2. Three edits in `switch.py`

**Edit 1.** Change the line `import serial` to:

```python
import socket
```

**Edit 2.** Replace the whole `alt_down` function with:

```python
alt_t = 0


def alt_down():
    global alt, alt_t
    if not alt:
        kb.press(Key.alt)
        alt = True
        time.sleep(0.01)
    alt_t = time.time()
```

**Edit 3.** Replace the whole `messages` function with:

```python
SECRET = "change-me"
PORT = 4210


def messages():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("", PORT))
    s.settimeout(1)
    print(f"Listening on UDP port {PORT}")
    prev, prev_t = "", 0
    while True:
        try:
            data, _ = s.recvfrom(64)
        except socket.timeout:
            if alt and time.time() - alt_t > 30:
                alt_up()
            continue
        text, now = data.decode(errors='ignore'), time.time()
        if text == prev and now - prev_t < 0.1:
            continue
        prev, prev_t = text, now
        key, _, m = text.partition(":")
        if key == SECRET:
            yield m
```

What it does: it listens for the ESP32's messages, ignores the duplicate copy, ignores anything without the right `SECRET`, and releases Alt by itself if a release message was ever lost (after 30 seconds).

### Part 3. Start it

1. Upload the new ESP32 code with the USB cable.
2. Run `python switch.py`. It prints `Listening on UDP port 4210`.
3. The first time, Windows asks to allow Python through the firewall. Tick **Private networks** (also **Public networks** if you use a hotspot) and click **Allow access**.
4. Unplug the USB data cable and power the ESP32 from a power bank. Click the button.

### Wi-Fi troubleshooting

| Problem | Fix |
|---|---|
| ESP32 never connects | Wi-Fi is 5 GHz only, wrong password, or WPA3. Use a 2.4 GHz WPA2 network |
| Connects but laptop sees nothing | Firewall prompt missed, or the network blocks device-to-device traffic. Use a phone hotspot |
| First click after a long idle is late | Normal for some routers. The ESP32 code already turns Wi-Fi sleep off |

The `SECRET` is sent as plain text. It stops accidents and pranks on a shared network, not a determined attacker. Keep shutdown and similar actions on high click counts.

## Upgrade ideas

| Upgrade | What it gives | Rough difficulty | What to change |
|---|---|---|---|
| **No-code settings window** | Anyone can set what each click does by choosing from menus and a Browse button for apps. No code visible | Medium | New `config.json` plus a small settings window (Python `tkinter`). `switch.py` reads the file at start |
| **Auto-find the COM port** | No need to edit `COM3` | Easy | Use `serial.tools.list_ports` and pick the board by its USB ID |
| More buttons | More shortcuts (for example one button per app) | Medium | One more pin per button, messages like `B:2` for button B |
| Click modes | 7 clicks cycles Work, Media, Presentation. Each mode has its own table | Easy | Keep a `mode` variable and one `ACTIONS` table per mode |
| App-aware clicks | Same click does different things in PowerPoint and Chrome | Medium | `pygetwindow` reads the title of the front window |
| New hold gestures | Hold 1.5 s peek, hold 4 s lock, click then hold, and so on | Medium | Firmware sends new messages (for example `H2`). Table handles them |
| Lights and sound | LED blink, beep or an OLED text on every click | Easy | Add output pins in the firmware |
| Smart home | Click to switch a light, plug or scene | Medium | `requests.get(url)` to IFTTT, Home Assistant or a smart plug |
| Own program, no Python needed | Share with friends | Medium | Package with PyInstaller into one `.exe` |
| macOS or Linux | More users | Medium | Replace `os.startfile`, `ctypes.windll`, Windows shortcuts |
| Battery | Fully wire-free | Medium | LiPo battery, charger board, ESP32 deep sleep that wakes on a button press |
| Proper enclosure | Looks like a product | Easy | 3D-printed case. Later a soldered board or a custom PCB |

### Design for the no-code settings window

Store the choices in a plain file:

```json
{
  "actions": {
    "1": {"type": "alt_tab", "times": 1},
    "2": {"type": "open", "target": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"},
    "3": {"type": "hotkey", "keys": ["cmd", "d"]},
    "4": {"type": "lock"}
  }
}
```

The settings window has one row per click count with a drop-down for the action type (open app or file, website, hotkey, power) and a **Browse** button that fills in the path. **Save** writes the file. `switch.py` loads it and builds the `ACTIONS` table from it, so users never open the code.

### Finding the COM port automatically

```python
from serial.tools import list_ports


def find_port():
    for p in list_ports.comports():
        if p.vid in (0x10C4, 0x1A86):
            return p.device
```

`0x10C4` is the chip family used on many ESP32 boards and `0x1A86` is another very common one. Use the returned name in place of `'COM3'`.
