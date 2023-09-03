import pylewm.commands
import pylewm.monitors
import time

# Note: this import is required here to make focus changing work for unknown reasons
import win32com.client

import pylewm.window
from pylewm.winproxy.winfocus import focus_window, focus_shell_window, get_cursor_position
from pylewm.commands import PyleCommand

FocusWindow = None
PreviousFocusWindow = None
FocusChangeTime = 0.0

FocusHistory = []
FocusFuture = []

@PyleCommand
def focus_monitor(monitor_index):
    monitor = pylewm.monitors.get_monitor_by_index(monitor_index)
    set_focus_space(monitor.visible_space)

@PyleCommand
def focus_history_previous():
    global FocusWindow
    global FocusHistory
    global FocusFuture

    for i in range(len(FocusHistory) - 1, -1, -1):
        if FocusHistory[i] == FocusWindow:
            continue
        if not FocusHistory[i]:
            continue
        if FocusHistory[i].closed:
            continue

        target_window = FocusHistory[i]

        FocusFuture = FocusHistory[i+1:] + FocusFuture
        FocusHistory = FocusHistory[:i+1]

        if len(FocusFuture) > 50:
            FocusFuture = FocusFuture[-50:]

        set_focus(target_window)
        break

@PyleCommand
def focus_history_next():
    global FocusWindow
    global FocusHistory
    global FocusFuture

    for i in range(0, len(FocusFuture) - 1):
        if FocusFuture[i] == FocusWindow:
            continue
        if not FocusFuture[i]:
            continue
        if FocusFuture[i].closed:
            continue

        target_window = FocusFuture[i]

        FocusHistory = FocusHistory + FocusFuture[:i+1]
        FocusFuture = FocusFuture[i+1:]

        if len(FocusHistory) > 50:
            FocusHistory = FocusHistory[-50:]

        set_focus(target_window)
        break

@PyleCommand
def focus_history_flip():
    global FocusWindow
    global FocusHistory

    for i in range(len(FocusHistory) - 1, -1, -1):
        if FocusHistory[i] == FocusWindow:
            continue
        if not FocusHistory[i]:
            continue
        if FocusHistory[i].closed:
            continue

        flip_window = FocusHistory[i]
        FocusHistory[i] = FocusWindow

        FocusHistory[-1] = flip_window
        set_focus(flip_window)

        break

def set_focus(window):
    global FocusWindow
    global PreviousFocusWindow
    global FocusChangeTime
    global FocusHistory

    assert isinstance(window, pylewm.window.Window)

    prev_focus = FocusWindow
    FocusWindow = window
    if FocusWindow != prev_focus:
        PreviousFocusWindow = prev_focus
        FocusChangeTime = time.time()

        if not FocusHistory or FocusHistory[-1] != FocusWindow:
            FocusHistory.append(FocusWindow)
            if len(FocusHistory) > 50:
                FocusHistory = FocusHistory[-50:]

    focus_window(window.proxy, move_mouse=True)

def set_focus_no_mouse(window):
    global FocusWindow
    global PreviousFocusWindow
    global FocusChangeTime

    prev_focus = FocusWindow
    FocusWindow = window
    if FocusWindow != prev_focus:
        PreviousFocusWindow = prev_focus
        FocusChangeTime = time.time()
    focus_window(window.proxy, move_mouse=False)

def set_focus_space(space):
    if space.last_focus:
        set_focus(space.last_focus)
    elif space.windows:
        set_focus(space.windows[0])
    else:
        set_focus_monitor(space.monitor)

def set_focus_space_no_mouse(space):
    if space.last_focus:
        set_focus_no_mouse(space.last_focus)
    elif space.windows:
        set_focus_no_mouse(space.windows[0])

def was_just_focused(window):
    if FocusWindow == window:
        return True
    if PreviousFocusWindow == window:
        if time.time() - FocusChangeTime < 0.2:
            return True
    return False

def set_focus_monitor(monitor):
    rect = monitor.rect.copy()
    focus_shell_window(rect)

def get_cursor_space():
    monitor = pylewm.monitors.get_monitor_at(get_cursor_position())
    if not monitor:
        monitor = pylewm.monitors.get_default_monitor()
    return monitor.visible_space

def get_focused_space():
    cursor_space = get_cursor_space()
    # If the mouse is on an empty space, use that space instead of the one that has a focused window
    # this is because random windows get focused when the last window loses focus.
    if len(cursor_space.windows) == 0:
        return cursor_space
    if FocusWindow and FocusWindow.space and FocusWindow.space.visible:
        return FocusWindow.space
    return cursor_space

def get_focused_monitor():
    space = get_focused_space()
    return space.monitor

def on_focus_changed(proxy):
    """ Message sent from the windows proxy thread that a new window proxy has received focus. """
    global FocusWindow
    global PreviousFocusWindow
    global FocusChangeTime
    global FocusHistory

    prev_focus = FocusWindow
    FocusWindow = pylewm.window.get_window(proxy)

    if FocusWindow != prev_focus:
        PreviousFocusWindow = prev_focus
        FocusChangeTime = time.time()

        if not FocusHistory or FocusHistory[-1] != FocusWindow:
            FocusHistory.append(FocusWindow)
            if len(FocusHistory) > 50:
                FocusHistory = FocusHistory[-50:]

import pylewm.winproxy.winfocus
pylewm.winproxy.winfocus.OnFocusChanged = on_focus_changed