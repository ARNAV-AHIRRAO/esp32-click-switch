import os
import time
import ctypes
import serial
from pynput.keyboard import Key, Controller

kb = Controller()
alt = False


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


def open_app(path):
    os.startfile(path)


def hotkey(*keys):
    for k in keys:
        kb.press(k)
        time.sleep(0.01)
    for k in reversed(keys):
        kb.release(k)
        time.sleep(0.01)


def run(cmd):
    os.system(cmd)


def web(url):
    os.startfile(url)


ACTIONS = {
    1: ("Alt+Tab x1", lambda: alt_tab(1)),
    2: ("Alt+Tab x2", lambda: alt_tab(2)),
    3: ("Alt+Tab x3", lambda: alt_tab(3)),
    4: ("Alt+Tab x4", lambda: alt_tab(4)),
    5: ("Alt+Tab x5", lambda: alt_tab(5)),
}


def messages():
    while True:
        try:
            ser = serial.Serial('COM3', 115200)
            print("Connected COM3")
            while True:
                yield ser.readline().decode(errors='ignore').strip()
        except serial.SerialException:
            alt_up()
            time.sleep(2)


try:
    for m in messages():
        if m == 'H':
            print("HOLD -> switcher open, release to pick")
            alt_down()
            tap(Key.tab)
        elif m == 'R':
            print("RELEASE -> window picked")
            alt_up()
        elif m.isdigit():
            n = int(m)
            if n in ACTIONS:
                name, fn = ACTIONS[n]
                print(f"{n} click{'s' * (n > 1)} -> {name}")
                fn()
            else:
                print(f"{n} clicks -> no action set")
finally:
    alt_up()
