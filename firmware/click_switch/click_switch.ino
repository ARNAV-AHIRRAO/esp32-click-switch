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

void send(String m) {
  Serial.println(m);
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN, INPUT_PULLUP);
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
