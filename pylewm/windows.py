from pylewm.commands import PyleThread, PyleCommand
from pylewm.window import Window
import pylewm.focus
import pylewm.window
import pylewm.monitors

import pylewm.window_classification

import ctypes

import win32gui
import win32api
import win32con

import traceback

IgnoredWindows = set()
Windows = {}
NewWindows = []
MinimizedWindows = set()

InitialPlacement = True

@PyleCommand.Threaded
def close():
    ''' Close the window that currently has focus. Whether that window is in a layout or not. '''
    hwnd = win32gui.GetForegroundWindow()
    if hwnd in Windows and Windows[hwnd]:
        window = Windows[hwnd]
        window.force_closed = True

        space = window.space
        if space:
            space.remove_window(window)
            pylewm.focus.set_focus_space(space)

        win32gui.PostMessage(win32gui.GetForegroundWindow(), win32con.WM_CLOSE, 0, 0)
    else:
        win32gui.PostMessage(win32gui.GetForegroundWindow(), win32con.WM_CLOSE, 0, 0)

@PyleCommand
def drop_window_into_layout():
    ''' Drop a previously unmanaged window into the layout of the monitor it's on. '''
    hwnd = win32gui.GetForegroundWindow()
    if hwnd in Windows and Windows[hwnd]:
        window = Windows[hwnd]
        if window.floating:
            window.floating = False
            window.can_tile = True
            window.take_new_rect = True

            space = pylewm.focus.get_cursor_space()
            drop_slot, force_drop = space.get_drop_slot(window.rect.center, window.rect)
            space.drop_into_slot(window, drop_slot)
    else:
        window = Window(hwnd)
        NewWindows.append(window)

@PyleCommand
def move_to_monitor(monitor_index):
    window = pylewm.focus.FocusWindow
    if not window or not window.space:
        return

    space = window.space
    monitor = pylewm.monitors.get_monitor_by_index(monitor_index)

    space.remove_window(window)
    monitor.visible_space.add_window(window)

@PyleCommand
def minimize():
    hwnd = win32gui.GetForegroundWindow()
    if hwnd in Windows and Windows[hwnd]:
        Windows[hwnd].minimize()
    else:
        pylewm.window.minimize_window_handle(hwnd)

@PyleCommand
def poke():
    if pylewm.focus.FocusWindow:
        pylewm.focus.FocusWindow.poke()

def reset_all():
    global Windows
    for window in Windows.values():
        if window:
            window.reset()
    Windows = {}

def print_window_info(window=None, text=None, indent=""):
    if window is None:
        window = win32gui.GetForegroundWindow()
    if text is None:
        text = "WINDOW"
    if not win32gui.IsWindow(window):
        print("NO WINDOW FOCUSED")
        return

    def show_flags(flags, flag_list):
        str = ""
        for i in range(0, 32):
            if flags & 1<<i:
                if str:
                    str += " | "

                found_flag = False
                for flag in flag_list:
                    if (1<<i) & flag[0]:
                        str += flag[1]
                        found_flag = True
                        break
                if not found_flag:
                    str += f"{(1<<i):x}".zfill(8)
        return str

    print(f"{indent}{text}")
    print(f"{indent}  Title: {win32gui.GetWindowText(window)}")
    print(f"{indent}  Class: {win32gui.GetClassName(window)}")
    print(f"{indent}  HWND: {window}   Parent: {win32api.GetWindowLong(window, win32con.GWL_HWNDPARENT)}")
    print(f"{indent}  Style: {show_flags(win32api.GetWindowLong(window, win32con.GWL_STYLE), WINDOW_STYLE_FLAGS)}"
        + f"  ExStyle: {show_flags(win32api.GetWindowLong(window, win32con.GWL_EXSTYLE), WINDOW_STYLE_EX_FLAGS)}")
    print(f"{indent}  Pos: {win32gui.GetWindowRect(window)}")

def add_window_to_space(window):
    # Find the monitor that this window is most on
    space = None

    filter_monitor = pylewm.filters.get_monitor(window)
    if filter_monitor != -1:
        filter_monitor = min(filter_monitor, len(pylewm.monitors.Monitors)-1)
        space = pylewm.monitors.Monitors[filter_monitor].visible_space
    elif InitialPlacement or window.handle in MinimizedWindows:
        monitor = pylewm.monitors.get_covering_monitor(window.rect)
        space = monitor.visible_space
    else:
        space = pylewm.focus.get_focused_space()

    # Add the window to the space that is visible on that monitor
    space.add_window(window)

def manage_window(window):
    pylewm.filters.trigger_all_filters(window, post=False)

    if not window.floating:
        add_window_to_space(window)

    window.manage()

    # Start managing the window
    if window.handle in MinimizedWindows:
        MinimizedWindows.remove(window.handle)

    pylewm.filters.trigger_all_filters(window, post=True)

@PyleThread(0.05)
def tick_windows():
    global NewWindows

    # Find any new windows we hadn't discovered before
    def enumUnknown(hwnd, param):
        try:
            if hwnd in Windows:
                if not Windows[hwnd] and pylewm.window.is_window_handle_minimized(hwnd):
                    # If a window we previously tracked is minimized, we remove our tracking block,
                    # this will make it pop back into the layout when we un-minimize automatically
                    del Windows[hwnd]
                    MinimizedWindows.add(hwnd)
                else:
                    return
            if hwnd in IgnoredWindows:
                return

            window, classification, reason = pylewm.window_classification.classify_window(hwnd)
            if classification == pylewm.window_classification.IgnoreTemporary:
                pass
            elif classification == pylewm.window_classification.IgnorePermanent:
                #print_window_info(hwnd, "IGNORE "+reason)
                IgnoredWindows.add(hwnd)
            elif classification == pylewm.window_classification.Tiled:
                window.floating = False
                NewWindows.append(window)
                print_window_info(window.handle, f"Classify as Tiled: "+str(reason))
            elif classification == pylewm.window_classification.Floating:
                window.floating = True
                window.can_tile = False
                NewWindows.append(window)
                print_window_info(window.handle, f"Classify as Floating: "+str(reason))
        except Exception as ex:
            # The window got destroyed in some way, so we should just ignore it
            IgnoredWindows.add(hwnd)
            #traceback.print_exc()

    win32gui.EnumWindows(enumUnknown, None)

    for window in NewWindows:
        Windows[window.handle] = window
        manage_window(window)
    NewWindows = []

    # Remove windows that have been closed
    for window in Windows.values():
        if not window:
            continue
        if window.closed:
            space = window.space
            if space:
                lost_index = space.windows.index(window)
                space.remove_window(window)
                if not window.force_closed and space.windows and space == pylewm.focus.get_cursor_space():
                    focus_window = space.windows[space.layout.get_focus_slot_after_removing(lost_index)]
                    pylewm.focus.set_focus(focus_window)
            window.stop_managing()
            Windows[window.handle] = None
        if window.floating and window.space:
            window.space.remove_window(window)

    # Update focus
    focus_hwnd = win32gui.GetForegroundWindow()
    if focus_hwnd in Windows and Windows[focus_hwnd]:
        if pylewm.focus.FocusWindow:
            pylewm.focus.FocusWindow.focused = False
        pylewm.focus.FocusWindow = Windows[focus_hwnd]
        if pylewm.focus.FocusWindow:
            pylewm.focus.FocusWindow.focused = True
    else:
        if pylewm.focus.FocusWindow:
            pylewm.focus.FocusWindow.focused = False
        pylewm.focus.FocusWindow = None

    if pylewm.focus.FocusWindow and not pylewm.focus.FocusWindow.closed:
        pylewm.focus.LastFocusWindow = pylewm.focus.FocusWindow
        pylewm.focus.FocusSpace = pylewm.focus.FocusWindow.space
        if pylewm.focus.FocusSpace and not pylewm.focus.FocusSpace.visible:
            pylewm.focus.FocusSpace = None
    else:
        pylewm.focus.FocusSpace = None

    if pylewm.focus.LastFocusWindow and pylewm.focus.LastFocusWindow.closed:
        pylewm.focus.LastFocusWindow = None
    if pylewm.focus.FocusWindow and pylewm.focus.FocusWindow.closed:
        pylewm.focus.FocusWindow.focused = False
        pylewm.focus.FocusWindow = None

    # Update spaces on all monitors
    for monitor in pylewm.monitors.Monitors:
        for space in monitor.spaces:
            space.update_layout(pylewm.focus.FocusWindow)
        for space in monitor.temp_spaces:
            space.update_layout(pylewm.focus.FocusWindow)

    # Update all windows
    for window in Windows.values():
        if not window:
            continue
        window.trigger_update()

    # We are no longer in initial placement mode
    global InitialPlacement
    InitialPlacement = False


WINDOW_STYLE_FLAGS = (
    (win32con.WS_BORDER, "WS_BORDER"),
    (win32con.WS_CAPTION, "WS_CAPTION"),
    (win32con.WS_CHILD, "WS_CHILD"),
    (win32con.WS_CLIPCHILDREN, "WS_CLIPCHILDREN"),
    (win32con.WS_CLIPSIBLINGS, "WS_CLIPSIBLINGS"),
    (win32con.WS_DISABLED, "WS_DISABLED"),
    (win32con.WS_DLGFRAME, "WS_DLGFRAME"),
    (win32con.WS_GROUP, "WS_GROUP"),
    (win32con.WS_HSCROLL, "WS_HSCROLL"),
    (win32con.WS_ICONIC, "WS_ICONIC"),
    (win32con.WS_MAXIMIZE, "WS_MAXIMIZE"),
    (win32con.WS_MAXIMIZEBOX, "WS_MAXIMIZEBOX"),
    (win32con.WS_MINIMIZE, "WS_MINIMIZE"),
    (win32con.WS_MINIMIZEBOX, "WS_MINIMIZEBOX"),
    (win32con.WS_OVERLAPPED, "WS_OVERLAPPED"),
    (win32con.WS_POPUP, "WS_POPUP"),
    (win32con.WS_SIZEBOX, "WS_SIZEBOX"),
    (win32con.WS_SYSMENU, "WS_SYSMENU"),
    (win32con.WS_TABSTOP, "WS_TABSTOP"),
    (win32con.WS_VISIBLE, "WS_VISIBLE"),
    (win32con.WS_VSCROLL, "WS_VSCROLL"),
)

WINDOW_STYLE_EX_FLAGS = (
)