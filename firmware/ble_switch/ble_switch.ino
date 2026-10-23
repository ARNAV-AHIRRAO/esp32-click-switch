/*
 * ESP32 BLE Click Switch - Native Bluetooth Low Energy Keyboard Mode
 * 
 * NO PYTHON OR PC SOFTWARE REQUIRED!
 * Turns your ESP32 into a native wireless Bluetooth HID keyboard.
 * Pairs directly with Windows, macOS, Linux, Android, iOS, iPadOS.
 *
 * Requirements:
 * - Install the "ESP32-BLE-Keyboard" library by T-vK:
 *   https://github.com/T-vK/ESP32-BLE-Keyboard
 *   (Download ZIP -> Arduino IDE -> Sketch -> Include Library -> Add .ZIP Library)
 */

#include <BleKeyboard.h>

const int PIN = 4;
const int LED_PIN = 2; // Built-in blue LED for connection & click feedback

const unsigned long DEBOUNCE = 25;
const unsigned long GAP = 300;
const unsigned long HOLD_1 = 1500;  // 1.5s -> Task Switcher Peek
const unsigned long HOLD_2 = 4000;  // 4.0s -> Instant PC Lock

int last = HIGH;
int count = 0;
int held = 0;  // 0 = none, 1 = stage 1 hold, 2 = stage 2 hold
bool altHeld = false;

unsigned long t = 0;
unsigned long tPress = 0;
unsigned long tRelease = 0;
unsigned long lastBlink = 0;
bool ledState = false;

// Create BLE Keyboard device with custom name and manufacturer
BleKeyboard bleKeyboard("ESP32 Click Switch", "DIY", 100);

void setup() {
  Serial.begin(115200);
  pinMode(PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  Serial.println("Starting BLE Click Switch...");
  bleKeyboard.begin();
}

void releaseAltIfHeld() {
  if (altHeld) {
    bleKeyboard.release(KEY_LEFT_ALT);
    altHeld = false;
  }
}

void executeClickAction(int clicks) {
  if (!bleKeyboard.isConnected()) return;

  Serial.print("BLE Action for clicks: ");
  Serial.println(clicks);

  switch (clicks) {
    case 1:
      // Alt+Tab once (quick jump to last window)
      bleKeyboard.press(KEY_LEFT_ALT);
      delay(15);
      bleKeyboard.write(KEY_TAB);
      delay(15);
      bleKeyboard.release(KEY_LEFT_ALT);
      break;

    case 2:
      // Alt+Tab twice
      bleKeyboard.press(KEY_LEFT_ALT);
      delay(15);
      bleKeyboard.write(KEY_TAB);
      delay(40);
      bleKeyboard.write(KEY_TAB);
      delay(15);
      bleKeyboard.release(KEY_LEFT_ALT);
      break;

    case 3:
      // Show Desktop (Win + D)
      bleKeyboard.press(KEY_LEFT_GUI);
      delay(15);
      bleKeyboard.write('d');
      delay(15);
      bleKeyboard.release(KEY_LEFT_GUI);
      break;

    case 4:
      // Media Play / Pause
      bleKeyboard.write(KEY_MEDIA_PLAY_PAUSE);
      break;

    case 5:
      // Media Mute
      bleKeyboard.write(KEY_MEDIA_MUTE);
      break;

    default:
      Serial.println("No action mapped for this click count.");
      break;
  }
}

void loop() {
  unsigned long now = millis();

  // Connection indicator LED:
  // If not connected to Bluetooth, blink LED slowly (advertising mode)
  // If connected, LED stays solid/off and lights up on button press
  if (!bleKeyboard.isConnected()) {
    if (now - lastBlink > 500) {
      lastBlink = now;
      ledState = !ledState;
      digitalWrite(LED_PIN, ledState ? HIGH : LOW);
    }
  }

  int r = digitalRead(PIN);

  // Debounce and state transition
  if (r != last && now - t > DEBOUNCE) {
    t = now;
    last = r;

    if (r == LOW) {
      tPress = now;
      if (bleKeyboard.isConnected()) digitalWrite(LED_PIN, HIGH);
    } else if (held > 0) {
      // Released after hold
      if (held == 1 && bleKeyboard.isConnected()) {
        releaseAltIfHeld();
        Serial.println("Released Stage 1 Hold (Window picked)");
      }
      held = 0;
      if (bleKeyboard.isConnected()) digitalWrite(LED_PIN, LOW);
    } else {
      count++;
      tRelease = now;
      if (bleKeyboard.isConnected()) digitalWrite(LED_PIN, LOW);
    }
  }

  // Stage 1 Hold: Task Switcher opens and stays open while held
  if (last == LOW && held == 0 && now - tPress > HOLD_1) {
    held = 1;
    count = 0;
    if (bleKeyboard.isConnected()) {
      Serial.println("Stage 1 Hold: Holding Alt+Tab");
      bleKeyboard.press(KEY_LEFT_ALT);
      delay(15);
      bleKeyboard.write(KEY_TAB);
      altHeld = true;
      digitalWrite(LED_PIN, HIGH);
    }
  }

  // Stage 2 Hold: Emergency/Panic Lock PC (Win + L)
  if (last == LOW && held == 1 && now - tPress > HOLD_2) {
    held = 2;
    releaseAltIfHeld();
    if (bleKeyboard.isConnected()) {
      Serial.println("Stage 2 Hold: Emergency Lock PC");
      // Double flash LED to confirm stage 2 trigger
      digitalWrite(LED_PIN, LOW); delay(60);
      digitalWrite(LED_PIN, HIGH); delay(60);
      digitalWrite(LED_PIN, LOW); delay(60);
      digitalWrite(LED_PIN, HIGH);

      // Lock Workstation (Win + L)
      bleKeyboard.press(KEY_LEFT_GUI);
      delay(15);
      bleKeyboard.write('l');
      delay(15);
      bleKeyboard.release(KEY_LEFT_GUI);
    }
  }

  // Click burst finalized
  if (count > 0 && last == HIGH && now - tRelease > GAP) {
    executeClickAction(count);
    count = 0;
  }
}
