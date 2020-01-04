from pylewm.window import Window

import win32gui
import win32api
import win32con

Ignore = 0
Manage = 1
Postpone = 2

IGNORED_CLASSES = {
    "windows.ui.core.corewindow", # Always directly under an ApplicationFrameWindow, so safe to ignore
    "progman",
}

IGNORED_WINDOWS = {
    "program manager", # The desktop window
}

def classify_window(hwnd):
    # Invisible windows are ignored until they become visible
    if not win32gui.IsWindowVisible(hwnd):
        return None, Postpone, "Invisible"

    window = Window(hwnd)
    style = win32api.GetWindowLong(hwnd, win32con.GWL_STYLE)
    exStyle = win32api.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)

    # Windows with 0 size are not managed
    if window.rect.height == 0 or window.rect.width == 0:
        return window, Ignore, "Zero Size"

    # Some hard-coded ignore classes and titles
    if window.window_class.lower() in IGNORED_CLASSES:
        return window, Ignore, "Ignored Class"
    if window.window_title.lower() in IGNORED_CLASSES:
        return window, Ignore, "Ignored Title"

    # Windows that aren't resizable are ignored,
    # we can usually assume these aren't available for tiling.
    if not (style & win32con.WS_SIZEBOX):
        return window, Ignore, "No Resize"

    # NOACTIVATE windows that aren't APPWINDOW are ignored by
    # the taskbar, so we probably should ignore them as well
    if (exStyle & win32con.WS_EX_NOACTIVATE) and not (exStyle & win32con.WS_EX_APPWINDOW):
        return window, Ignore, "Not AppWindow"

    return window, Manage, None