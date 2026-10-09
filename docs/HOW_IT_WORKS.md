# How It Works

This page follows one full life of the project in order: uploading the code, powering up, starting Python, and finally what happens on every click, down to the key presses Windows receives.

## The big picture

```
 [Button] --wire--> [ESP32 pin D4] ---- firmware counts clicks ----+
                                                                   |
                                          USB cable (serial text: "2")
                                                                   |
 [Windows] <--key presses-- [switch.py: pyserial reads, pynput types] <+
```

Two programs cooperate:

| Program | Lives in | Job |
|---|---|---|
| `click_switch.ino` | The ESP32 chip | Watches the button. Counts clicks. Sends short text messages over USB |
| `switch.py` | Your laptop | Reads those messages. Presses keys or runs actions on Windows |

The ESP32 never knows what a click means. It only reports "2 clicks". The laptop decides what 2 clicks do. That is why you can change the meaning of clicks without re-uploading anything.

## The messages the ESP32 sends

Each message is one line of text:

| Message | Meaning |
|---|---|
| `1`, `2`, `3` ... | The button was clicked that many times in a quick row |
| `H` | The button has been held down for 1.5 seconds |
| `R` | The button was released after a hold |

## Phase 1. When you press Upload in Arduino IDE

1. Arduino IDE translates `click_switch.ino` into machine code the ESP32 understands (this is called compiling).
2. The IDE talks to the small USB chip on the ESP32 board. That chip turns USB signals into the serial signals the ESP32 main chip uses.
3. The IDE briefly toggles two control lines (RTS and DTR) which reset the ESP32 into "download mode" (the reason a stuck upload sometimes needs the BOOT button).
4. The machine code is written into the ESP32's flash memory.
5. `Hard resetting via RTS pin` means the IDE reset the chip again so it starts the new program.

The program is now stored permanently in flash. It runs every time the ESP32 gets power. No laptop software is needed for this part.

## Phase 2. Every time the ESP32 powers on

1. The ESP32 boots and starts your program.
2. `setup()` runs once:
   - `Serial.begin(115200)` opens the serial line to the USB chip at 115200 bits per second.
   - `pinMode(PIN, INPUT_PULLUP)` turns pin D4 (GPIO4) into an input and switches on a tiny resistor inside the chip that connects D4 to 3.3 volts.
3. With the button not pressed, D4 is pulled up to 3.3 volts. The ESP32 reads this as **HIGH**.
4. `loop()` now runs over and over, thousands of times per second, doing three checks.

## Phase 3. When you run `python switch.py`

1. Python reads the file from top to bottom: imports the libraries, creates the keyboard controller (`kb`), defines the helper functions, builds the `ACTIONS` table.
2. The line `for m in messages():` starts the `messages()` function.
3. `messages()` opens the USB port with `serial.Serial('COM3', 115200)`. Opening the port usually makes the ESP32 restart once (the same control lines as above), so wait about a second.
4. Python prints `Connected COM3` and waits at `ser.readline()`. It does nothing until a full line of text arrives.

## Phase 4. What happens when you click twice

Follow the current and the data from your finger to the screen.

**Electrical (inside the circuit)**

```
ESP32 3.3 V --(internal pull-up resistor)--> D4 pin --> orange wire --> button leg E58
                                                                            |  (pressing joins the diagonal legs)
ESP32 GND pin <-- black wire <-- button leg F60 <--------------------------+
```

- Not pressed: nothing joins the legs. D4 sits at 3.3 V. Reading is HIGH.
- Pressed: the legs touch. D4 is connected straight to GND (0 V). A tiny current (well under 1 milliamp) flows through the internal pull-up resistor. Reading is LOW.

**Firmware (inside the ESP32), clicking twice quickly**

| Time | What you do | What the code does |
|---|---|---|
| 0 ms | Press 1 | `digitalRead` gives LOW. It differs from `last` and the last change was more than 25 ms ago (`DEBOUNCE`), so the change is accepted. `last = LOW`, `tPress = now` |
| 90 ms | Release 1 | Reading is HIGH. Accepted. Not a hold, so `count++` makes `count = 1`. `tRelease = now` |
| 200 ms | Press 2 | Accepted as before. `tPress = now` |
| 290 ms | Release 2 | `count++` makes `count = 2`. `tRelease = now` |
| 590 ms | You wait | 300 ms (`GAP`) have passed since the last release. The code runs `send(String(count))`. This prints `2` plus a line break to the serial line. `count` goes back to 0 |

Why the 300 ms wait: the ESP32 cannot know you are finished until a short quiet gap passes. That is the small delay you feel after the last click.

Why the 25 ms filter (`DEBOUNCE`): real buttons flicker on and off for a few milliseconds when pressed. The filter ignores that flicker so one press counts as one click.

**Data on the way to the laptop**

1. `Serial.println("2")` sends the characters `2`, carriage return, line feed to the USB chip.
2. The USB chip sends them through the USB cable.
3. Windows delivers them to the COM port.
4. `ser.readline()` in Python wakes up once it sees the line feed. `.decode()` turns bytes into text. `.strip()` removes the line break. `m` is now the text `"2"`.

**Python (inside the laptop)**

1. `m == 'H'`? No. `m == 'R'`? No. `m.isdigit()`? Yes.
2. `n = int(m)` makes `n = 2`.
3. `2 in ACTIONS`? Yes. `name, fn = ACTIONS[2]` gives `"Alt+Tab x2"` and the small function behind it.
4. It prints `2 clicks -> Alt+Tab x2`.
5. `fn()` runs `alt_tab(2)`:

| Step | Code | What Windows receives |
|---|---|---|
| 1 | `alt_down()` | Alt key pressed down. `alt = True` remembers it |
| 2 | `tap(Key.tab)` | Tab pressed, 10 ms, Tab released. The window switcher appears and highlights the previous window |
| 3 | `tap(Key.tab)` | Tab again. The highlight moves to the next window |
| 4 | `alt_up()` | Alt released. Windows switches to the highlighted window |

`pynput` creates these key presses the same way a real keyboard would, so Windows cannot tell the difference.

## Phase 5. What happens when you hold the button

| Time | What happens | Code that runs |
|---|---|---|
| 0 ms | You press and keep holding | `tPress = now` |
| 1500 ms | Still held | `last == LOW && !held && now - tPress > HOLD` becomes true. `held = 1`, `count = 0`, `send("H")` |
| 1500 ms | Laptop gets `H` | Python prints `HOLD -> switcher open, release to pick`, runs `alt_down()` then `tap(Key.tab)`. Alt stays pressed. The window switcher stays on screen |
| any time | You look and choose | The switcher stays open because Alt is still held by the script |
| You let go | Release is accepted | Because `held` is set, the ESP32 sends `R` instead of counting a click, and sets `held = 0` |
| right after | Laptop gets `R` | Python prints `RELEASE -> window picked`, runs `alt_up()`. Windows switches to the highlighted window |

## Safety nets in `switch.py`

| Situation | What the code does |
|---|---|
| You stop the program (Ctrl+C) | The `finally:` block runs `alt_up()` so Alt never stays stuck |
| USB cable is unplugged | `readline()` raises an error. The `except` block runs `alt_up()`, waits 2 seconds and tries to reconnect, forever |
| Click count with no action in the table (for example 8 clicks) | Prints `8 clicks -> no action set` and does nothing |
| `alt_down()` called twice | The `alt` flag stops it pressing Alt twice |

## The ESP32 code in plain words

| Name | Meaning |
|---|---|
| `PIN = 4` | The button is on pin D4 (GPIO4) |
| `DEBOUNCE = 25` | Ignore changes that come within 25 ms of the last accepted change |
| `GAP = 300` | After the last click, wait 300 ms before reporting the count |
| `HOLD = 1500` | Holding for 1.5 seconds counts as a hold, not a click |
| `last` | The last accepted button state (HIGH = up, LOW = down) |
| `count` | Clicks counted so far in the current burst |
| `held` | 1 if a hold has already been reported |
| `t`, `tPress`, `tRelease` | Time stamps in milliseconds: last accepted change, last press, last release |
| `send(m)` | Sends the text `m` to the laptop. Only this function would change for wireless |

You can change `DEBOUNCE`, `GAP` and `HOLD` and upload again. Raise `GAP` if fast clickers get split counts. Lower it for a quicker response.

## The Python code in plain words

| Function | What it does |
|---|---|
| `tap(k)` | Press and release one key |
| `alt_down()`, `alt_up()` | Press or release Alt, and remember which |
| `alt_tab(n)` | Hold Alt, tap Tab `n` times, release Alt |
| `show_desktop()` | Windows key + D |
| `sleep_pc()` | Puts the laptop to sleep |
| `open_app(path)` | Opens a program, file, folder or website |
| `hotkey(*keys)` | Press several keys together (like Ctrl+Shift+Esc), then release |
| `run(cmd)` | Runs a command like a Command Prompt would |
| `web(url)` | Opens a web address |
| `ACTIONS` | The table: clicks, name, action. This is the part you edit |
| `messages()` | Opens the port, yields each line the ESP32 sends, reconnects if the cable is pulled |

The last block of the file is the main loop. It takes each message and decides: hold, release, or click count.
