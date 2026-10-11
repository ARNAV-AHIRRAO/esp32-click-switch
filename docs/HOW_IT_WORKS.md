# How It Works

This page follows the program from the moment you start it to the moment Windows switches window.

## The big picture

```
Webcam --> MediaPipe finds 21 points on your hand --> count raised fingers
      --> state rules (2 fingers? 3+ fingers?) --> pyautogui presses Alt / Tab
      --> Windows shows the switcher and switches
```

Everything lives in one file, `gesture_worker.py`. It has two parts:

| Part | Name in the code | Job |
|---|---|---|
| Tray app | `PrivacyGestureApp` | The blue **G** icon and its menu. Switches gestures on and off |
| Camera worker | `run_gesture_detection` | Opens the camera, finds your hand, counts fingers, presses keys |

The worker runs in its own separate process, so the camera and the hand-finder never freeze the tray icon.

## Phase 1. When you start the program

1. Python loads the libraries: OpenCV (camera), MediaPipe (hand finder), pyautogui (key presses), pystray (tray icon), Pillow (draws the icon picture).
2. `MODEL_PATH` points to `hand_landmarker.task`. In the `.exe` version the model is packed inside the file, and `resource_path` finds it in the temporary folder where the `.exe` unpacks itself.
3. The last lines call `PrivacyGestureApp().start()`. The tray icon appears. Nothing else is running yet and the camera is off.

## Phase 2. When you click the icon (Enable gestures)

1. `toggle` runs. Gestures are off, so it calls `enable()`.
2. `enable()` creates a stop signal (`stop_event`) and starts a new process that runs `run_gesture_detection`.
3. The icon tooltip changes to **Privacy Gesture, On**.
4. Inside the worker, setup happens once:
   - The hand-finding model is loaded with these settings: one hand, running mode `VIDEO` (it follows the hand from picture to picture), confidence 0.50.
   - The camera opens at 640 by 480. If the camera cannot open, the worker ends quietly.
   - Counters start at zero: `two_finger_frames`, `three_plus_finger_frames`, `gesture_held`, `select_gesture_held`, `alt_tab_active`, `last_tab_time`.

## Phase 3. What happens for every camera picture (many times per second)

| Step | Code | What it means |
|---|---|---|
| 1 | `cap.read()` | Grab one picture from the camera |
| 2 | `cv2.flip(frame, 1)` | Mirror it, so moving your hand right looks like moving right |
| 3 | `cv2.cvtColor` | Convert colours to the order MediaPipe expects |
| 4 | `landmarker.detect_for_video` | MediaPipe returns 21 points for your hand (wrist, knuckles, joints, fingertips) |
| 5 | `count_extended_fingers` | For each of 4 fingers, is the fingertip higher on screen than its middle joint? Yes means the finger is up. The thumb is not counted |
| 6 | Gesture rules (below) | Decide what to do with the finger count |
| 7 | Drawing | Green dots on fingertips and status text on the picture |
| 8 | `cv2.imshow`, `cv2.waitKey(1)` | Show the picture and check keys: Enter, Esc, Q |

The fingertip and joint points used are: index 8 and 6, middle 12 and 10, ring 16 and 14, pinky 20 and 18 (MediaPipe's numbering). This is why your hand must be upright: the test is "tip above joint".

## The gesture rules

```
finger count >= 3  ->  count frames. After CONFIRM_FRAMES (2) in a row: select_window()
finger count == 2  ->  count frames. After CONFIRM_FRAMES (2) in a row, and only once
                       per raise (gesture_held): press_tab()
anything else      ->  reset all counters so a new gesture can start
```

`press_tab()`:

| Situation | Keys sent |
|---|---|
| Less than `GESTURE_COOLDOWN` (0.25 s) since the last Tab | Nothing |
| Alt is not held yet (`alt_tab_active` is false) | Alt goes down, Tab is pressed, `alt_tab_active = True` |
| Alt is already held | Only Tab is pressed |

`select_window()`: if Alt is held, release it (Windows then switches to the highlighted window), and reset all counters. If Alt was not held, it does nothing, so showing 3 fingers by accident is harmless.

Why "once per raise": `gesture_held` stays true while you keep 2 fingers up. It resets only when you show something else (fist, 1 finger, 3 fingers). That is why you lower your hand between two "next window" steps.

## Phase 4. Example: go two windows back

Times are rough, assuming the camera gives about 30 pictures a second.

| Time | You do | What the program does | What Windows does |
|---|---|---|---|
| 0.00 s | Raise 2 fingers | Picture 1: `two_finger_frames = 1` | Nothing yet |
| 0.03 s | Still 2 fingers | Picture 2: reaches `CONFIRM_FRAMES`. `press_tab()`: Alt down, Tab | Switcher opens, previous window highlighted |
| 1.00 s | Make a fist | Counters reset. `gesture_held = False`. Alt stays down | Switcher stays open |
| 1.50 s | Raise 2 fingers again | After 2 pictures: `press_tab()`, Tab only | Highlight moves to the next window |
| 2.20 s | Show 3 fingers | After 2 pictures: `select_window()`, Alt goes up | Windows switches to the highlighted window |

The key presses come from `pyautogui`, which sends them the same way a real keyboard does. Windows cannot tell the difference.

## Turning it off

| Action | What happens |
|---|---|
| **Disable gestures** in the tray menu | `stop_event` is set. The worker loop ends. The `finally:` block releases Alt if it was held, closes the camera and the window |
| Press **Q** in the camera window | Same clean stop of the worker. The tray icon stays |
| **Exit** in the tray menu | Disables gestures, then closes the tray icon |
| Camera cannot open | The worker ends. Click **Enable gestures** again after freeing the camera |

The `finally:` block is a safety net: Alt is never left pressed when the worker stops.

## The settings in plain words

| Name | Value | Meaning |
|---|---|---|
| `DETECTION_CONFIDENCE` | 0.50 | How sure MediaPipe must be that it sees a hand |
| `PRESENCE_CONFIDENCE` | 0.50 | How sure it must be that the hand is still there |
| `TRACKING_CONFIDENCE` | 0.50 | How sure it must be when following the hand between pictures |
| `CONFIRM_FRAMES` | 2 | A gesture must last this many pictures in a row |
| `GESTURE_COOLDOWN` | 0.25 | Minimum seconds between two Tab presses |
| `CAMERA_WIDTH`, `CAMERA_HEIGHT` | 640, 480 | Camera picture size. Small pictures mean faster detection |

## Good to know

- The on-screen text says "ESC = CANCEL", but in the code Esc calls the same function as Enter. It lets go of Alt, so the highlighted window is picked. The fix is in [UPGRADES.md](UPGRADES.md).
- If you show 2 fingers and then leave your hand down, Alt stays held until you show 3 fingers, press Enter, or disable gestures. An optional auto-release fix is in [UPGRADES.md](UPGRADES.md).
- The keys Enter, Esc and Q only work while the camera window is the window in front.
