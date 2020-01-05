import pylewm.monitors
import pylewm.window

import win32gui
import win32api
import win32con

IgnorePermanent = 0
IgnoreTemporary = 1
Tiled = 2
Floating = 3

def classify_window(hwnd):
    # Invisible windows are ignored until they become visible
    if not win32gui.IsWindowVisible(hwnd):
        return None, IgnoreTemporary, "Invisible"

    # Cloaked windows are not handled
    if pylewm.window.is_window_handle_cloaked(hwnd):
        return None, IgnoreTemporary, "Cloaked"

    style = win32api.GetWindowLong(hwnd, win32con.GWL_STYLE)
    exStyle = win32api.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    window = pylewm.window.Window(hwnd)

    # Windows with no title are temporary and should be ignored
    if window.window_title == '':
        return None, IgnoreTemporary, "Empty Title"

    # Don't bother with windows that don't overlap the desktop at all
    if not window.rect.overlaps(pylewm.monitors.DesktopArea):
        return None, IgnoreTemporary, "Off Screen"

    # Windows with 0 size are not managed
    if window.rect.height == 0 or window.rect.width == 0:
        return window, IgnorePermanent, "Zero Size"

    # NOACTIVATE windows that aren't APPWINDOW are ignored by
    # the taskbar, so we probably should ignore them as well
    if (exStyle & win32con.WS_EX_NOACTIVATE) and not (exStyle & win32con.WS_EX_APPWINDOW):
        return window, IgnorePermanent, "Not AppWindow"

    # Windows that aren't resizable are ignored,
    # we can usually assume these aren't available for tiling.
    if not (style & win32con.WS_SIZEBOX):
        return window, Floating, "No Resize"

    return window, Tiled, None