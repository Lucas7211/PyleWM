import pylewm.commands
import pylewm.monitors
import pythoncom
import win32gui, win32com.client
import win32api
import traceback
import ctypes

from pylewm.window import Window, get_window
from pylewm.winproxy.winfocus import focus_window, focus_shell_window, get_cursor_position
from pylewm.commands import PyleCommand

FocusWindow : Window = None
LastFocusWindow : Window = None

@PyleCommand
def focus_monitor(monitor_index):
    monitor = pylewm.monitors.get_monitor_by_index(monitor_index)
    set_focus_space(monitor.visible_space)

def set_focus(window):
    global FocusWindow
    global LastFocusWindow

    FocusWindow = window
    LastFocusWindow = window
    focus_window(window.proxy, move_mouse=True)

def set_focus_no_mouse(window):
    global FocusWindow
    global LastFocusWindow

    FocusWindow = window
    LastFocusWindow = window
    focus_window(window.proxy, move_mouse=False)

def set_focus_space(space):
    if space.last_focus:
        set_focus(space.last_focus)
    elif space.windows:
        set_focus(space.windows[0])
    else:
        set_focus_monitor(space.monitor)

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
    global LastFocusWindow

    FocusWindow = get_window(proxy)
    if FocusWindow and not FocusWindow.is_ignored():
        LastFocusWindow = FocusWindow

import pylewm.winproxy.winfocus
pylewm.winproxy.winfocus.OnFocusChanged = on_focus_changed