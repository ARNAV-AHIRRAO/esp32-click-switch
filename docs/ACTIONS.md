# Action List: What a Click Can Do

## How to use this page

1. Open `software/switch.py` and find the `ACTIONS` block.
2. Pick the number of clicks you want (for example `3`).
3. Copy a line from the "Code" column below, and put it after the number.
4. Save the file and run the program again.

Format of one line:

```python
3: ("Show desktop", lambda: hotkey(Key.cmd, 'd')),
```

The three parts are: click count, a name that is printed on screen, and the action. Every action must start with `lambda:`, except plain function names such as `show_desktop` or `sleep_pc`.

A full example table:

```python
ACTIONS = {
    1: ("Alt+Tab x1", lambda: alt_tab(1)),
    2: ("Alt+Tab x2", lambda: alt_tab(2)),
    3: ("Show desktop", show_desktop),
    4: ("Open Chrome", lambda: open_app(r"C:\Program Files\Google\Chrome\Application\chrome.exe")),
    5: ("Play / pause", lambda: tap(Key.media_play_pause)),
    9: ("Lock PC", lambda: ctypes.windll.user32.LockWorkStation()),
}
```

Safety tip: put risky actions (shutdown, restart, sign out, close window) on high click counts such as 7, 8 or 9. Then an accidental double click can never trigger them.

Helper functions already in `switch.py`: `tap`, `hotkey`, `run`, `web`, `open_app`, `alt_tab`, `show_desktop`, `sleep_pc`.

## Power

| Action | Code |
|---|---|
| Lock | `lambda: ctypes.windll.user32.LockWorkStation()` |
| Shutdown in 15 seconds | `lambda: run("shutdown /s /t 15")` |
| Cancel shutdown | `lambda: run("shutdown /a")` |
| Restart in 15 seconds | `lambda: run("shutdown /r /t 15")` |
| Hibernate | `lambda: run("shutdown /h")` |
| Sleep | `sleep_pc` |
| Sign out | `lambda: run("shutdown /l")` |
| Screen off | `lambda: ctypes.windll.user32.SendMessageW(0xFFFF, 0x0112, 0xF170, 2)` |
| Task Manager | `lambda: hotkey(Key.ctrl, Key.shift, Key.esc)` |

If the laptop hibernates when you expect sleep, open Command Prompt as administrator and run `powercfg -h off`.

## Windows

| Action | Code |
|---|---|
| Show desktop | `lambda: hotkey(Key.cmd, 'd')` |
| Task view | `lambda: hotkey(Key.cmd, Key.tab)` |
| Close window | `lambda: hotkey(Key.alt, Key.f4)` |
| Minimize window | `lambda: hotkey(Key.cmd, Key.down)` |
| Maximize window | `lambda: hotkey(Key.cmd, Key.up)` |
| Snap window left | `lambda: hotkey(Key.cmd, Key.left)` |
| Snap window right | `lambda: hotkey(Key.cmd, Key.right)` |
| Minimize all | `lambda: hotkey(Key.cmd, 'm')` |
| Next virtual desktop | `lambda: hotkey(Key.ctrl, Key.cmd, Key.right)` |
| Previous virtual desktop | `lambda: hotkey(Key.ctrl, Key.cmd, Key.left)` |
| New virtual desktop | `lambda: hotkey(Key.ctrl, Key.cmd, 'd')` |
| Close virtual desktop | `lambda: hotkey(Key.ctrl, Key.cmd, Key.f4)` |
| Move window to other monitor | `lambda: hotkey(Key.cmd, Key.shift, Key.right)` |
| Project / extend screen | `lambda: hotkey(Key.cmd, 'p')` |
| File Explorer | `lambda: hotkey(Key.cmd, 'e')` |
| Settings | `lambda: hotkey(Key.cmd, 'i')` |
| Run box | `lambda: hotkey(Key.cmd, 'r')` |
| Search | `lambda: hotkey(Key.cmd, 's')` |
| Clipboard history | `lambda: hotkey(Key.cmd, 'v')` |
| Voice typing | `lambda: hotkey(Key.cmd, 'h')` |
| Snip screenshot | `lambda: hotkey(Key.cmd, Key.shift, 's')` |
| Full screenshot to file | `lambda: hotkey(Key.cmd, Key.print_screen)` |

## Browser (Chrome or Edge in front)

| Action | Code |
|---|---|
| Close tab | `lambda: hotkey(Key.ctrl, 'w')` |
| New tab | `lambda: hotkey(Key.ctrl, 't')` |
| Reopen closed tab | `lambda: hotkey(Key.ctrl, Key.shift, 't')` |
| Next tab | `lambda: hotkey(Key.ctrl, Key.tab)` |
| Previous tab | `lambda: hotkey(Key.ctrl, Key.shift, Key.tab)` |
| Refresh | `lambda: tap(Key.f5)` |
| Hard refresh | `lambda: hotkey(Key.ctrl, Key.shift, 'r')` |
| Incognito window | `lambda: hotkey(Key.ctrl, Key.shift, 'n')` |
| Back | `lambda: hotkey(Key.alt, Key.left)` |
| Forward | `lambda: hotkey(Key.alt, Key.right)` |
| Address bar | `lambda: hotkey(Key.ctrl, 'l')` |
| Bookmark page | `lambda: hotkey(Key.ctrl, 'd')` |
| Zoom in | `lambda: hotkey(Key.ctrl, '=')` |
| Zoom out | `lambda: hotkey(Key.ctrl, '-')` |
| Reset zoom | `lambda: hotkey(Key.ctrl, '0')` |
| Fullscreen | `lambda: tap(Key.f11)` |
| Developer tools | `lambda: tap(Key.f12)` |
| Open a website | `lambda: web("https://youtube.com")` |

## Media

| Action | Code |
|---|---|
| Play / pause | `lambda: tap(Key.media_play_pause)` |
| Next track | `lambda: tap(Key.media_next)` |
| Previous track | `lambda: tap(Key.media_previous)` |
| Volume up | `lambda: tap(Key.media_volume_up)` |
| Volume down | `lambda: tap(Key.media_volume_down)` |
| Mute | `lambda: tap(Key.media_volume_mute)` |
| Volume up big | `lambda: [tap(Key.media_volume_up) for _ in range(5)]` |
| Open Spotify | `lambda: web("spotify:")` |
| YouTube in front: pause or play | `lambda: tap('k')` |
| YouTube in front: forward 10 seconds | `lambda: tap('l')` |
| YouTube in front: back 10 seconds | `lambda: tap('j')` |

## Editing and typing

| Action | Code |
|---|---|
| Copy | `lambda: hotkey(Key.ctrl, 'c')` |
| Paste | `lambda: hotkey(Key.ctrl, 'v')` |
| Cut | `lambda: hotkey(Key.ctrl, 'x')` |
| Paste as plain text | `lambda: hotkey(Key.ctrl, Key.shift, 'v')` |
| Undo | `lambda: hotkey(Key.ctrl, 'z')` |
| Redo | `lambda: hotkey(Key.ctrl, 'y')` |
| Save | `lambda: hotkey(Key.ctrl, 's')` |
| Select all | `lambda: hotkey(Key.ctrl, 'a')` |
| Find | `lambda: hotkey(Key.ctrl, 'f')` |
| Type your email, phone or signature | `lambda: kb.type("hello@example.com")` |

Never put passwords here. The text is stored in plain form in the file and is typed into whichever window is in front.

## Meetings (meeting window in front)

| App | Action | Code |
|---|---|---|
| Google Meet | Mute | `lambda: hotkey(Key.ctrl, 'd')` |
| Google Meet | Camera | `lambda: hotkey(Key.ctrl, 'e')` |
| Zoom | Mute | `lambda: hotkey(Key.alt, 'a')` |
| Zoom | Camera | `lambda: hotkey(Key.alt, 'v')` |
| Teams | Mute | `lambda: hotkey(Key.ctrl, Key.shift, 'm')` |
| Teams | Camera | `lambda: hotkey(Key.ctrl, Key.shift, 'o')` |

## Slide clicker (great for presentations)

| Action | Code |
|---|---|
| Next slide | `lambda: tap(Key.right)` |
| Previous slide | `lambda: tap(Key.left)` |
| Start slideshow | `lambda: tap(Key.f5)` |
| End slideshow | `lambda: tap(Key.esc)` |
| Black screen | `lambda: tap('b')` |
| White screen | `lambda: tap('w')` |

## Apps, files and links

| Action | Code |
|---|---|
| Any program | `lambda: open_app(r"C:\Path\app.exe")` |
| Notepad | `lambda: open_app("notepad")` |
| Calculator | `lambda: open_app("calc")` |
| Paint | `lambda: open_app("mspaint")` |
| Command Prompt | `lambda: open_app("cmd")` |
| Snipping Tool | `lambda: open_app("snippingtool")` |
| A folder or a file | `lambda: open_app(r"C:\Users\<YourName>\Downloads")` |
| VS Code on a project | `lambda: run('code "C:\\myproject"')` |
| Bluetooth settings | `lambda: open_app("ms-settings:bluetooth")` |
| Display settings | `lambda: open_app("ms-settings:display")` |
| Run a .bat or .py script | `lambda: run(r'python "C:\scripts\x.py"')` |
| A Store app | `lambda: open_app("shell:AppsFolder\\<AppID>")` |

To find the `<AppID>` of a Store app, open PowerShell and run `Get-StartApps`.

## Extra ideas (need a little more code)

| Idea | How |
|---|---|
| Speak the time or battery level | `pip install pyttsx3` |
| Save a screenshot to a file | `pip install pyautogui` |
| Log every click with a time stamp to a CSV file | Python `csv` module |
| Trigger a smart plug, light or IFTTT recipe | `pip install requests`, then `requests.get(url)` |
| Send a Telegram message ("I am here", alert) | Telegram bot plus `requests` |
| Switch dark or light mode | `reg add` command on the Personalize registry key |
| Change laptop brightness | `run('powershell -c "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,30)"')` |
| 25 minute focus timer | Python `threading.Timer` |
| Panic combo: mute, show desktop, lock in one click | One `lambda` that runs three actions |
| Same click, different action per app (PowerPoint: next slide, Chrome: next tab) | `pip install pygetwindow` to read the front window |
| Modes: 7 clicks cycles Work, Media, Presentation, each with its own table | See [UPGRADES.md](UPGRADES.md) |
| Hold for 4 seconds to lock | Needs a small firmware change. See [UPGRADES.md](UPGRADES.md) |
