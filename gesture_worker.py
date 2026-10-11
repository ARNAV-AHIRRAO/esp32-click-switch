import multiprocessing
import os
import sys
import time

import cv2
import mediapipe as mp
import pyautogui
import pystray
from PIL import Image, ImageDraw
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

DETECTION_CONFIDENCE = 0.50
PRESENCE_CONFIDENCE = 0.50
TRACKING_CONFIDENCE = 0.50

CONFIRM_FRAMES = 2
GESTURE_COOLDOWN = 0.25

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480


def resource_path(filename):
    base_folder = getattr(
        sys,
        "_MEIPASS",
        os.path.dirname(os.path.abspath(__file__)),
    )
    return os.path.join(base_folder, filename)


MODEL_PATH = resource_path("hand_landmarker.task")


def run_gesture_detection(stop_event):
    options = vision.HandLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=DETECTION_CONFIDENCE,
        min_hand_presence_confidence=PRESENCE_CONFIDENCE,
        min_tracking_confidence=TRACKING_CONFIDENCE,
    )

    landmarker = vision.HandLandmarker.create_from_options(options)

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        landmarker.close()
        return

    two_finger_frames = 0
    three_plus_finger_frames = 0
    gesture_held = False
    select_gesture_held = False
    alt_tab_active = False
    last_tab_time = 0.0
    start_time = time.time()

    def finger_extended(hand, tip, pip):
        return hand[tip].y < hand[pip].y

    def count_extended_fingers(hand):
        count = 0

        if finger_extended(hand, 8, 6):
            count += 1

        if finger_extended(hand, 12, 10):
            count += 1

        if finger_extended(hand, 16, 14):
            count += 1

        if finger_extended(hand, 20, 18):
            count += 1

        return count

    def press_tab():
        nonlocal alt_tab_active, last_tab_time

        now = time.time()

        if now - last_tab_time < GESTURE_COOLDOWN:
            return

        if not alt_tab_active:
            pyautogui.keyDown("alt")
            pyautogui.press("tab")
            alt_tab_active = True
        else:
            pyautogui.press("tab")

        last_tab_time = now

    def select_window():
        nonlocal alt_tab_active
        nonlocal gesture_held
        nonlocal select_gesture_held
        nonlocal two_finger_frames
        nonlocal three_plus_finger_frames

        if alt_tab_active:
            pyautogui.keyUp("alt")
            alt_tab_active = False

        gesture_held = False
        select_gesture_held = False
        two_finger_frames = 0
        three_plus_finger_frames = 0

    def cancel_selection():
        select_window()

    try:
        while not stop_event.is_set():
            ok, frame = cap.read()

            if not ok:
                continue

            frame = cv2.flip(frame, 1)

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=rgb,
            )

            timestamp_ms = int((time.time() - start_time) * 1000)

            result = landmarker.detect_for_video(
                mp_image,
                timestamp_ms,
            )

            finger_count = 0
            hand = None

            if result.hand_landmarks:
                hand = result.hand_landmarks[0]
                finger_count = count_extended_fingers(hand)

            if finger_count >= 3:
                three_plus_finger_frames += 1
                two_finger_frames = 0
                gesture_held = False

                if (
                    three_plus_finger_frames >= CONFIRM_FRAMES
                    and not select_gesture_held
                ):
                    select_gesture_held = True
                    select_window()

                cv2.putText(
                    frame,
                    "3+ FINGERS = SELECT",
                    (15, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 255, 0),
                    2,
                )

            elif finger_count == 2:
                three_plus_finger_frames = 0
                select_gesture_held = False
                two_finger_frames += 1

                if two_finger_frames >= CONFIRM_FRAMES and not gesture_held:
                    gesture_held = True
                    press_tab()

                cv2.putText(
                    frame,
                    "2 FINGERS = NEXT WINDOW",
                    (15, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 255, 255),
                    2,
                )

            else:
                two_finger_frames = 0
                three_plus_finger_frames = 0
                gesture_held = False
                select_gesture_held = False

            if hand is not None:
                height, width, _ = frame.shape

                for tip in [8, 12, 16, 20]:
                    x = int(hand[tip].x * width)
                    y = int(hand[tip].y * height)

                    cv2.circle(
                        frame,
                        (x, y),
                        8,
                        (0, 255, 0),
                        -1,
                    )

            if alt_tab_active:
                cv2.putText(
                    frame,
                    "ALT+TAB ACTIVE",
                    (15, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.60,
                    (0, 255, 255),
                    2,
                )

                cv2.putText(
                    frame,
                    "2 FINGERS NEXT | 3+ SELECT",
                    (15, 105),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.52,
                    (255, 255, 255),
                    2,
                )
            else:
                cv2.putText(
                    frame,
                    "READY",
                    (15, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.60,
                    (255, 255, 255),
                    2,
                )

            cv2.putText(
                frame,
                "ESC = CANCEL | Q = STOP",
                (15, 140),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.50,
                (255, 255, 255),
                2,
            )

            cv2.imshow("Privacy Gesture", frame)

            key = cv2.waitKey(1) & 0xFF

            if key == 13:
                select_window()

            elif key == 27:
                cancel_selection()

            elif key == ord("q"):
                break

    finally:
        if alt_tab_active:
            pyautogui.keyUp("alt")

        cap.release()
        landmarker.close()
        cv2.destroyAllWindows()


class PrivacyGestureApp:
    def __init__(self):
        self.process = None
        self.stop_event = None

        self.icon = pystray.Icon(
            "Privacy Gesture",
            self.create_icon(),
            "Privacy Gesture — Off",
            self.create_menu(),
        )

    def create_icon(self):
        image = Image.new("RGB", (64, 64), "#1f2937")
        drawing = ImageDraw.Draw(image)

        drawing.ellipse((8, 8, 56, 56), fill="#2563eb")
        drawing.text((24, 19), "G", fill="white")

        return image

    def is_enabled(self):
        return self.process is not None and self.process.is_alive()

    def create_menu(self):
        return pystray.Menu(
            pystray.MenuItem(
                lambda item: (
                    "Disable gestures" if self.is_enabled() else "Enable gestures"
                ),
                self.toggle,
                default=True,
            ),
            pystray.MenuItem("Exit", self.exit_app),
        )

    def enable(self):
        if self.is_enabled():
            return

        self.stop_event = multiprocessing.Event()

        self.process = multiprocessing.Process(
            target=run_gesture_detection,
            args=(self.stop_event,),
        )

        self.process.start()

        self.icon.title = "Privacy Gesture — On"
        self.icon.update_menu()

    def disable(self):
        if self.stop_event:
            self.stop_event.set()

        if self.process:
            self.process.join(timeout=3)

        self.process = None
        self.stop_event = None

        self.icon.title = "Privacy Gesture — Off"
        self.icon.update_menu()

    def toggle(self, icon, item):
        if self.is_enabled():
            self.disable()
        else:
            self.enable()

    def exit_app(self, icon, item):
        self.disable()
        self.icon.stop()

    def start(self):
        self.icon.run()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    PrivacyGestureApp().start()
