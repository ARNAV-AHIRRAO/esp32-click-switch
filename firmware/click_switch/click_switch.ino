const int PIN = 4;
const int LED_PIN = 2; // Built-in blue LED on most ESP32 DevKit boards

const unsigned long DEBOUNCE = 25;
const unsigned long GAP = 300;
const unsigned long HOLD_1 = 1500;  // Stage 1 Hold: Task Switcher peek
const unsigned long HOLD_2 = 4000;  // Stage 2 Hold: Emergency/Panic action

int last = HIGH;
int count = 0;
int held = 0;  // 0 = none, 1 = hold stage 1 ("H"), 2 = hold stage 2 ("H2")

unsigned long t = 0;
unsigned long tPress = 0;
unsigned long tRelease = 0;

void send(String m) {
  Serial.println(m);
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
}

void loop() {
  int r = digitalRead(PIN);
  unsigned long now = millis();

  // Button state change with debounce filter
  if (r != last && now - t > DEBOUNCE) {
    t = now;
    last = r;

    if (r == LOW) {
      tPress = now;
      digitalWrite(LED_PIN, HIGH); // Visual feedback: LED on while pressed
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

  // Stage 1 Hold (e.g. 1.5 seconds)
  if (last == LOW && held == 0 && now - tPress > HOLD_1) {
    held = 1;
    count = 0;
    digitalWrite(LED_PIN, HIGH);
    send("H");
  }

  // Stage 2 Hold (e.g. 4.0 seconds - Panic / Emergency)
  if (last == LOW && held == 1 && now - tPress > HOLD_2) {
    held = 2;
    // Quick double blink on LED to signal Stage 2 triggered
    digitalWrite(LED_PIN, LOW);
    delay(60);
    digitalWrite(LED_PIN, HIGH);
    delay(60);
    digitalWrite(LED_PIN, LOW);
    delay(60);
    digitalWrite(LED_PIN, HIGH);
    send("H2");
  }

  // Clicks burst complete: wait for GAP after the last release
  if (count > 0 && last == HIGH && now - tRelease > GAP) {
    send(String(count));
    count = 0;
  }
}

