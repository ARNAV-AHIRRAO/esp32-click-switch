import ctypes
import json
import os
import sys
import threading
import time
import serial
from serial.tools import list_ports
from pynput.keyboard import Controller, Key

try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False

# Keyboard controller & state
kb = Controller()
alt = False
is_paused = False
is_running = True
current_port = "None"
is_connected = False
tray_icon = None

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
config_mtime = 0

KEY_MAP = {
    "alt": Key.alt,
    "alt_l": Key.alt_l,
    "alt_r": Key.alt_r,
    "cmd": Key.cmd,
    "win": Key.cmd,
    "ctrl": Key.ctrl,
    "shift": Key.shift,
    "esc": Key.esc,
    "tab": Key.tab,
    "enter": Key.enter,
    "space": Key.space,
    "backspace": Key.backspace,
    "delete": Key.delete,
    "up": Key.up,
    "down": Key.down,
    "left": Key.left,
    "right": Key.right,
    "home": Key.home,
    "end": Key.end,
    "page_up": Key.page_up,
    "page_down": Key.page_down,
    "print_screen": Key.print_screen,
    "f1": Key.f1,
    "f2": Key.f2,
    "f3": Key.f3,
    "f4": Key.f4,
    "f5": Key.f5,
    "f6": Key.f6,
    "f7": Key.f7,
    "f8": Key.f8,
    "f9": Key.f9,
    "f10": Key.f10,
    "f11": Key.f11,
    "f12": Key.f12,
}

MEDIA_MAP = {
    "play_pause": Key.media_play_pause,
    "next": Key.media_next,
    "prev": Key.media_previous,
    "vol_up": Key.media_volume_up,
    "vol_down": Key.media_volume_down,
    "mute": Key.media_volume_mute,
}


def tap(k):
    kb.press(k)
    time.sleep(0.01)
    kb.release(k)
    time.sleep(0.01)


def alt_down():
    global alt
    if not alt:
        kb.press(Key.alt)
        alt = True
        time.sleep(0.01)


def alt_up():
    global alt
    if alt:
        kb.release(Key.alt)
        alt = False


def alt_tab(n):
    alt_down()
    for _ in range(n):
        tap(Key.tab)
    alt_up()


def show_desktop():
    kb.press(Key.cmd)
    time.sleep(0.01)
    tap('d')
    kb.release(Key.cmd)


def sleep_pc():
    ctypes.windll.PowrProf.SetSuspendState(0, 1, 0)


def lock_pc():
    ctypes.windll.user32.LockWorkStation()


def screen_off():
    ctypes.windll.user32.SendMessageW(0xFFFF, 0x0112, 0xF170, 2)


def open_app(path):
    os.startfile(path)


def web(url):
    os.startfile(url)


def run_cmd(cmd):
    os.system(cmd)


def hotkey(*keys):
    for k in keys:
        kb.press(k)
        time.sleep(0.01)
    for k in reversed(keys):
        kb.release(k)
        time.sleep(0.01)


def resolve_key(k_str):
    k_lower = str(k_str).lower()
    return KEY_MAP.get(k_lower, k_str)


def parse_action(spec):
    if not isinstance(spec, dict):
        return None

    a_type = spec.get("type")

    if a_type == "alt_tab":
        times = int(spec.get("times", 1))
        return lambda: alt_tab(times)

    elif a_type == "hotkey":
        keys = [resolve_key(k) for k in spec.get("keys", [])]
        return lambda: hotkey(*keys)

    elif a_type == "media":
        cmd = spec.get("command", "play_pause")
        media_key = MEDIA_MAP.get(cmd, Key.media_play_pause)
        return lambda: tap(media_key)

    elif a_type == "open":
        target = spec.get("target", "")
        return lambda: open_app(target)

    elif a_type == "web":
        url = spec.get("target", "")
        return lambda: web(url)

    elif a_type == "power":
        cmd = spec.get("command", "lock")
        if cmd == "lock":
            return lock_pc
        elif cmd == "sleep":
            return sleep_pc
        elif cmd == "screen_off":
            return screen_off
        elif cmd == "shutdown":
            return lambda: run_cmd("shutdown /s /t 15")
        return lock_pc

    elif a_type == "type":
        text = spec.get("text", "")
        return lambda: kb.type(text)

    elif a_type == "run":
        cmd = spec.get("command", "")
        return lambda: run_cmd(cmd)

    elif a_type == "switcher_peek":
        return None

    return None


ACTIONS = {}
GESTURES = {}
SETTINGS = {}


def load_config():
    global ACTIONS, GESTURES, SETTINGS, config_mtime

    if not os.path.exists(CONFIG_PATH):
        # Fallback defaults if config.json was removed
        ACTIONS = {
            1: ("Alt+Tab x1", lambda: alt_tab(1)),
            2: ("Alt+Tab x2", lambda: alt_tab(2)),
            3: ("Show Desktop", show_desktop),
            4: ("Play / Pause", lambda: tap(Key.media_play_pause)),
            5: ("Mute Audio", lambda: tap(Key.media_volume_mute)),
            9: ("Lock PC", lock_pc),
        }
        GESTURES = {
            "hold_2": ("Lock PC", lock_pc),
            "rotary_cw": ("Volume Up", lambda: tap(Key.media_volume_up)),
            "rotary_ccw": ("Volume Down", lambda: tap(Key.media_volume_down)),
        }
        return

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        config_mtime = os.path.getmtime(CONFIG_PATH)
        SETTINGS = data.get("settings", {})

        new_actions = {}
        for count_str, spec in data.get("actions", {}).items():
            if count_str.isdigit():
                fn = parse_action(spec)
                name = spec.get("name", f"Action {count_str}")
                if fn:
                    new_actions[int(count_str)] = (name, fn)
        ACTIONS = new_actions

        new_gestures = {}
        for g_name, spec in data.get("gestures", {}).items():
            fn = parse_action(spec)
            name = spec.get("name", g_name)
            if fn:
                new_gestures[g_name] = (name, fn)
        GESTURES = new_gestures

        print(f"[Config] Loaded {len(ACTIONS)} click actions and {len(GESTURES)} gestures from config.json")
    except Exception as e:
        print(f"[Config] Error loading config.json: {e}")


def check_config_reload():
    global config_mtime
    if os.path.exists(CONFIG_PATH):
        mtime = os.path.getmtime(CONFIG_PATH)
        if mtime > config_mtime:
            print("[Config] File change detected, reloading...")
            load_config()


def find_esp32_port():
    """Auto-detects ESP32 COM port by standard USB VIDs."""
    configured_port = SETTINGS.get("port", "auto")
    if configured_port and configured_port.lower() != "auto":
        return configured_port

    known_vids = {0x10C4, 0x1A86, 0x303A, 0x0403}  # CP210x, CH340, Espressif native, FTDI
    available = list(list_ports.comports())

    # 1. Match by Vendor ID
    for p in available:
        if p.vid in known_vids:
            return p.device

    # 2. Match by description
    for p in available:
        desc = (p.description or "").lower()
        if "cp210" in desc or "ch340" in desc or "esp32" in desc or "serial" in desc:
            return p.device

    # 3. Fallback to first port or COM3
    if available:
        return available[0].device
    return "COM3"


def create_tray_image(connected, paused):
    """Draws a clean 64x64 icon for the system tray."""
    img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if not connected:
        bg = (100, 100, 100, 255)  # Gray
    elif paused:
        bg = (240, 140, 0, 255)   # Amber
    else:
        bg = (0, 140, 240, 255)   # Blue

    # Base circle
    draw.ellipse((4, 4, 60, 60), fill=bg)
    # Inner push button design
    draw.ellipse((18, 18, 46, 46), fill=(255, 255, 255, 230))
    draw.ellipse((24, 24, 40, 40), fill=bg)
    return img


def update_tray():
    global tray_icon
    if tray_icon and HAS_TRAY:
        try:
            tray_icon.icon = create_tray_image(is_connected, is_paused)
            status_text = f"ESP32: {current_port} ({'Connected' if is_connected else 'Disconnected'})"
            if is_paused:
                status_text += " [PAUSED]"
            tray_icon.title = status_text
        except Exception:
            pass


def toggle_pause(icon, item):
    global is_paused
    is_paused = not is_paused
    state_str = "PAUSED" if is_paused else "RESUMED"
    print(f"\n[Switch] {state_str}")
    update_tray()


def on_reload_config(icon, item):
    load_config()


def on_open_config(icon, item):
    if os.path.exists(CONFIG_PATH):
        os.startfile(CONFIG_PATH)


def on_exit(icon, item):
    global is_running
    is_running = False
    alt_up()
    if icon:
        icon.stop()


def start_tray():
    global tray_icon
    if not HAS_TRAY or not SETTINGS.get("system_tray", True):
        return

    menu = pystray.Menu(
        pystray.MenuItem(lambda text: f"Port: {current_port} ({'Connected' if is_connected else 'Disconnected'})", None, enabled=False),
        pystray.MenuItem(lambda text: "Resume Shortcuts" if is_paused else "Pause Shortcuts", toggle_pause),
        pystray.MenuItem("Reload Configuration", on_reload_config),
        pystray.MenuItem("Open config.json", on_open_config),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Exit", on_exit),
    )

    tray_icon = pystray.Icon("ESP32 Click Switch", create_tray_image(False, False), "ESP32 Click Switch", menu)
    tray_thread = threading.Thread(target=tray_icon.run, daemon=True)
    tray_thread.start()


def messages():
    global current_port, is_connected

    while is_running:
        check_config_reload()
        port = find_esp32_port()
        current_port = port
        baud = int(SETTINGS.get("baudrate", 115200))

        try:
            ser = serial.Serial(port, baud, timeout=1)
            is_connected = True
            update_tray()
            print(f"\n==========================================")
            print(f" Connected to ESP32 on {port} ({baud} baud)")
            print(f" Ready! Click your switch to trigger actions.")
            print(f"==========================================")

            while is_running:
                line = ser.readline().decode(errors="ignore").strip()
                if line:
                    yield line
                else:
                    check_config_reload()

        except (serial.SerialException, OSError):
            is_connected = False
            update_tray()
            alt_up()
            time.sleep(2)


def main():
    load_config()
    start_tray()

    try:
        for m in messages():
            if not is_running:
                break

            check_config_reload()

            if is_paused:
                print(f"[PAUSED] Ignored signal: {m}")
                continue

            # Stage 1 Hold: Task Switcher open
            if m == "H":
                print("HOLD Stage 1 -> Task switcher open (release to pick)")
                alt_down()
                tap(Key.tab)

            # Release after Stage 1 Hold: Pick active window
            elif m == "R":
                print("RELEASE -> Window picked")
                alt_up()

            # Stage 2 Hold: Emergency / Panic Action (e.g. 4s Hold)
            elif m == "H2":
                alt_up()
                if "hold_2" in GESTURES:
                    name, fn = GESTURES["hold_2"]
                    print(f"HOLD Stage 2 (Panic) -> {name}")
                    fn()
                else:
                    print("HOLD Stage 2 (Panic) -> Lock PC")
                    lock_pc()

            # Release after Stage 2 Hold
            elif m == "R2":
                alt_up()

            # Rotary Encoder: Clockwise
            elif m == "CW":
                if "rotary_cw" in GESTURES:
                    name, fn = GESTURES["rotary_cw"]
                    print(f"Rotary CW -> {name}")
                    fn()
                else:
                    tap(Key.media_volume_up)

            # Rotary Encoder: Counter-Clockwise
            elif m == "CCW":
                if "rotary_ccw" in GESTURES:
                    name, fn = GESTURES["rotary_ccw"]
                    print(f"Rotary CCW -> {name}")
                    fn()
                else:
                    tap(Key.media_volume_down)

            # Standard Clicks (1, 2, 3...)
            elif m.isdigit():
                n = int(m)
                if n in ACTIONS:
                    name, fn = ACTIONS[n]
                    print(f"{n} click{'s' * (n > 1)} -> {name}")
                    fn()
                else:
                    print(f"{n} clicks -> no action set in config.json")
    finally:
        alt_up()
        if tray_icon:
            tray_icon.stop()


if __name__ == "__main__":
    main()
