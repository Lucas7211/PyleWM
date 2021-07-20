import pylewm.monitors
import pylewm.window
import pylewm.filters

import win32gui
import win32api
import win32con

ALWAYS_IGNORE_TITLES = {
    "PyleWM_Internal",
}

ALWAYS_IGNORE_CLASSES = {
    "progman",
    "ime",
}

ALWAYS_FLOATING_CLASSES = {
    "operationstatuswindow",
    "#32770"
}

class WindowState:
    IgnorePermanent = 0
    IgnoreTemporary = 1
    Tiled = 2
    Floating = 3
    Unknown = 4

    def name(value):
        if value == WindowState.IgnorePermanent:
            return "IgnorePermanent"
        elif value == WindowState.IgnoreTemporary:
            return "IgnoreTemporary"
        elif value == WindowState.Tiled:
            return "Tiled"
        elif value == WindowState.Floating:
            return "Floating"
        elif value == WindowState.Unknown:
            return "Unknown"

def classify_window(window):
    # Special always ignored classes
    window_class = window.window_class.lower()
    if window_class in ALWAYS_IGNORE_CLASSES:
        return WindowState.IgnorePermanent, "Ignored Class"

    # NOACTIVATE windows that aren't APPWINDOW are ignored by
    # the taskbar, so we probably should ignore them as well
    if window.window_info.is_taskbar_ignored():
        return WindowState.IgnorePermanent, "Not AppWindow"

    # Check if any filters ignore this
    if pylewm.filters.is_ignored(window):
        return WindowState.IgnorePermanent, "Ignored by Filter"

    # Invisible windows are ignored until they become visible
    if not window.window_info.visible:
        return WindowState.IgnoreTemporary, "Invisible"

    # Cloaked windows are not handled
    if window.window_info.cloaked:
        return WindowState.IgnoreTemporary, "Cloaked"

    # Windows with no title are temporary and should be ignored
    if window.window_title == '':
        return WindowState.IgnoreTemporary, "Empty Title"

    # Windows with 0 size are not managed
    if window.real_position.height == 0 or window.real_position.width == 0:
        return WindowState.IgnorePermanent, "Zero Size"

    # Windows with no title are temporary and should be ignored
    if window.window_title in ALWAYS_IGNORE_TITLES:
        return WindowState.IgnoreTemporary, "Always Ignored by Name"

    # Don't bother with windows that don't overlap the desktop at all
    if not window.real_position.overlaps(pylewm.monitors.DesktopArea):
        return WindowState.IgnoreTemporary, "Off Screen"

    # Windows that aren't resizable are ignored,
    # we can usually assume these aren't available for tiling.
    if not window.window_info.can_resize():
        return WindowState.Floating, "No Resize"

    # Some classes that Windows uses should always be realistically floating
    if window_class in ALWAYS_FLOATING_CLASSES:
        return WindowState.Floating, "Floating Class"

    return WindowState.Tiled, None