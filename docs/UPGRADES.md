# Small Fixes and Upgrade Ideas

Nothing here is needed to use the program. Open `gesture_worker.py` in a text editor to try the fixes.

## Two small fixes

### Fix 1. Make Esc really cancel

Now, Esc lets go of Alt, so the highlighted window is picked. To make Esc close the switcher without switching, find this part:

```python
    def cancel_selection():
        select_window()
```

and replace it with:

```python
    def cancel_selection():
        if alt_tab_active:
            pyautogui.press("esc")
        select_window()
```

Pressing Esc while Alt is held closes the Windows switcher. Then Alt is released, and no window changes.

### Fix 2. Let go of Alt by itself after 8 seconds

Find the line `frame = cv2.flip(frame, 1)` inside the `while not stop_event.is_set():` loop. Put these two lines just above it, with the same indentation:

```python
            if alt_tab_active and time.time() - last_tab_time > 8:
                select_window()
```

If you open the switcher and then forget it, Alt is released after 8 seconds and Windows switches to the highlighted window. Change `8` to any number of seconds you like.

## Upgrade ideas

| Idea | What you get | Difficulty | How |
|---|---|---|---|
| Different action per finger count | 1 finger opens an app, 2 does Alt+Tab, and so on, like the click table in the `main` branch | Medium | A table of finger count to action. `pyautogui.hotkey(...)` for shortcuts and `os.startfile(...)` for apps |
| Settings window | Change sensitivity and actions with sliders and buttons, no code | Medium | Small window with `tkinter`, settings saved in a `config.json` file |
| Pick the camera | Works on laptops with several cameras | Easy | Replace `cv2.VideoCapture(0)` with another number, or add a menu entry in the tray |
| More gestures | Thumbs up, victory sign, open palm, swipe | Medium | MediaPipe has a ready Gesture Recognizer. Needs a second model file |
| Swipe gesture | Move your hand quickly to the side to switch (like the very first version) | Medium | Compare the wrist position over the last few pictures |
| Both hands | Left hand for next window, right hand for select | Medium | `num_hands=2` and read each hand's label |
| App-aware gestures | The same gesture does different things in PowerPoint and Chrome | Medium | `pygetwindow` reads the title of the front window |
| Lower CPU use | Cooler laptop, better battery | Easy | Lower the camera size, or only look at every second picture |
| Camera on screen indicator | Clear sign that the camera is on | Easy | Tray icon colour that changes when enabled |
| Start with Windows | Always ready | Easy but careful | Put a shortcut in `shell:startup`. Test the gestures and cooldown thoroughly first |
| macOS and Linux | More users | Medium | Alt+Tab becomes Command+Tab on macOS. Replace the Windows-only parts |
| Add a physical button | A button on the desk as well as gestures | Medium | See the ESP32 version in the `main` branch. Both can share the same action table |

## Ideas for a no-code settings file

```json
{
  "camera": 0,
  "confirm_frames": 2,
  "cooldown_seconds": 0.25,
  "gestures": {
    "2": {"action": "alt_tab_next"},
    "3": {"action": "alt_tab_select"},
    "1": {"action": "open", "target": "C:\\Windows\\System32\\notepad.exe"}
  }
}
```

The program would read this file when it starts. A small settings window would let anyone edit it without touching the code.
