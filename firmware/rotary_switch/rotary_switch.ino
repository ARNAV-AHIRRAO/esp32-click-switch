/*
 * ESP32 Rotary Click Switch
 * 
 * Combines an EC11 Rotary Encoder with the Click Switch logic:
 * - Rotate knob clockwise: Sends "CW" (e.g. Volume Up / Scrub Forward / Next Window)
 * - Rotate knob counter-clockwise: Sends "CCW" (e.g. Volume Down / Scrub Back / Prev Window)
 * - Press knob: Standard 1-click, 2-click, and Hold (1.5s switcher peek, 4s lock)
 * 
 * Pinout:
 * - Encoder CLK -> GPIO 18
 * - Encoder DT  -> GPIO 19
 * - Encoder SW  -> GPIO 4 (push button)
 * - Encoder GND -> ESP32 GND
 * - Encoder + / VCC -> ESP32 3.3V (if board has pullup resistors, or uses internal pullup)
 */

const int PIN_SW = 4;
const int PIN_CLK = 18;
const int PIN_DT = 19;
const int LED_PIN = 2;

const unsigned long DEBOUNCE = 25;
const unsigned long GAP = 300;
const unsigned long HOLD_1 = 1500;
const unsigned long HOLD_2 = 4000;

int lastSW = HIGH;
int count = 0;
int held = 0;

unsigned long t = 0;
unsigned long tPress = 0;
unsigned long tRelease = 0;

int lastClkState;

void send(String m) {
  Serial.println(m);
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_SW, INPUT_PULLUP);
  pinMode(PIN_CLK, INPUT_PULLUP);
  pinMode(PIN_DT, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  lastClkState = digitalRead(PIN_CLK);
}

void loop() {
  unsigned long now = millis();

  // --- 1. ROTARY ENCODER ROTATION ---
  int clkState = digitalRead(PIN_CLK);
  if (clkState != lastClkState && clkState == LOW) {
    // CLK changed state, check DT state to determine direction
    if (digitalRead(PIN_DT) != clkState) {
      send("CW"); // Clockwise
    } else {
      send("CCW"); // Counter-Clockwise
    }
    // Quick flash on LED for encoder tick
    digitalWrite(LED_PIN, HIGH);
    delayMicroseconds(500);
    digitalWrite(LED_PIN, LOW);
  }
  lastClkState = clkState;

  // --- 2. SWITCH BUTTON LOGIC ---
  int r = digitalRead(PIN_SW);

  if (r != lastSW && now - t > DEBOUNCE) {
    t = now;
    lastSW = r;

    if (r == LOW) {
      tPress = now;
      digitalWrite(LED_PIN, HIGH);
    } else if (held > 0) {
      if (held == 1) {
        send("R");
      } else {
        send("R2");
      }
      held = 0;
      digitalWrite(LED_PIN, LOW);
    } else {
      count++;
      tRelease = now;
      digitalWrite(LED_PIN, LOW);
    }
  }

  // Stage 1 Hold (1.5s)
  if (lastSW == LOW && held == 0 && now - tPress > HOLD_1) {
    held = 1;
    count = 0;
    digitalWrite(LED_PIN, HIGH);
    send("H");
  }

  // Stage 2 Hold (4.0s - Panic Lock)
  if (lastSW == LOW && held == 1 && now - tPress > HOLD_2) {
    held = 2;
    digitalWrite(LED_PIN, LOW); delay(60);
    digitalWrite(LED_PIN, HIGH); delay(60);
    digitalWrite(LED_PIN, LOW); delay(60);
    digitalWrite(LED_PIN, HIGH);
    send("H2");
  }

  // Finalize click burst
  if (count > 0 && lastSW == HIGH && now - tRelease > GAP) {
    send(String(count));
    count = 0;
  }
}
