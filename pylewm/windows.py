from pylewm.commands import PyleThread, PyleCommand
from pylewm.window import Window
import pylewm.monitors

import pylewm.window_classification

import win32gui
import win32api
import win32con

import traceback

IgnoredWindows = set()
Windows = {}

@PyleCommand.Threaded
def close():
    win32gui.PostMessage(win32gui.GetForegroundWindow(), win32con.WM_CLOSE, 0, 0)

def print_window_info(window=None, text=None, indent=""):
    if window is None:
        window = win32gui.GetForegroundWindow()
    if text is None:
        text = "WINDOW"
    if not win32gui.IsWindow(window):
        print("NO WINDOW FOCUSED")
        return

    print(f"{indent}{text}")
    print(f"{indent}  Title: {win32gui.GetWindowText(window)}")
    print(f"{indent}  Class: {win32gui.GetClassName(window)}")
    print(f"{indent}  HWND: {window}   Parent: {win32api.GetWindowLong(window, win32con.GWL_HWNDPARENT)}")
    print(f"{indent}  Style: {bin(win32api.GetWindowLong(window, win32con.GWL_STYLE))}"
        + f"  ExStyle: {bin(win32api.GetWindowLong(window, win32con.GWL_EXSTYLE))}")
    print(f"{indent}  Pos: {win32gui.GetWindowRect(window)}")

@PyleThread(0.05)
def tick_windows():
    # Find any new windows we hadn't discovered before
    new_windows = []
    def enumUnknown(hwnd, param):
        try:
            if hwnd in IgnoredWindows:
                return
            if hwnd in Windows:
                return

            window, classification, reason = pylewm.window_classification.classify_window(hwnd)
            if classification == pylewm.window_classification.Postpone:
                pass
            elif classification == pylewm.window_classification.Ignore:
                #print_window_info(hwnd, "IGNORE "+reason)
                IgnoredWindows.add(hwnd)
            elif classification == pylewm.window_classification.Manage:
                Windows[hwnd] = window
                new_windows.append(window)
        except Exception as ex:
            # The window got destroyed in some way, so we should just ignore it
            IgnoredWindows.add(hwnd)
            #traceback.print_exc()

    win32gui.EnumWindows(enumUnknown, None)

    for window in new_windows:
        # Find the monitor that this window is most on
        monitor = pylewm.monitors.get_covering_monitor(window.rect)

        # Add the window to the space that is visible on that monitor
        monitor.spaces[0].add_window(window)

        print_window_info(window.handle, "MANAGE ON DESKTOP "+str(monitor.spaces[0].rect))

        # Start managing the window
        window.manage()

    # Remove windows that have been closed

    # Update spaces on all monitors
    for monitor in pylewm.monitors.Monitors:
        for space in monitor.spaces:
            space.update_layout()
        for space in monitor.temp_spaces:
            space.update_layout()

    # Update all windows
    for window in Windows.values():
        window.trigger_update()
