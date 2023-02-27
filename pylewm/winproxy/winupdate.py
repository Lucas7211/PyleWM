import functools
import win32con
import time

import pylewm.winproxy.winfuncs as winfuncs
from pylewm.winproxy.windowproxy import WindowProxy, WindowsByHandle, ProxyCommands
from pylewm.commands import CommandQueue, Commands
from pylewm.window import Window, on_proxy_added, on_proxy_removed
from pylewm.winproxy.winfocus import update_focused_window
from pylewm.window_update import window_initial_placement

StartTime = None

def proxy_update():
    """ In charge of updating all interactions with the win32 world. """

    # Update what windows are tracked
    detect_new_windows()

    # Update which window is currently focused
    update_focused_window()

    # Perform updates on tracked windows if we need to
    update_tracked_windows()

    # Update global state in the application
    update_global_state()

def detect_new_windows():
    """ Detect any newly created windows that we aren't tracking. """

    def enum_window(hwnd, lparam):
        if hwnd in WindowsByHandle:
            return

        window = WindowProxy(hwnd)
        WindowsByHandle[hwnd] = window

    winfuncs.EnumWindows(winfuncs.tEnumWindowFunc(enum_window), 0)

def update_tracked_windows():
    """ Perform update logic for all windows that are currently tracked. """
    WindowProxy.UpdateFrameCounter += 1

    invalid_windows = []
    for hwnd, window in WindowsByHandle.items():
        if window.valid:
            if not window.initialized:
                window._initialize()
                Commands.queue(functools.partial(on_proxy_added, window))
            window._update()
        if not window.valid:
            invalid_windows.append(window)

    for window in invalid_windows:
        del WindowsByHandle[window._hwnd]
        Commands.queue(functools.partial(on_proxy_removed, window))

def update_global_state():
    # Window needs to know if left mouse button is down
    Window.IsLeftMouseHeld = (winfuncs.GetAsyncKeyState(win32con.VK_LBUTTON) != 0)

    # Record when we started updating
    global StartTime
    if StartTime is None:
        StartTime = time.time()

    # Trigger initial placement after our window proxies settle down
    if Window.InInitialPlacement and (time.time() - StartTime) > 0.1:
        all_initialized = True
        for hwnd, proxy in WindowsByHandle.items():
            if not proxy.initialized:
                all_initialized = False

        if all_initialized:
            Commands.queue(window_initial_placement)

def proxy_cleanup():
    """ Cleanup all proxies when the program is shutting down. """
    global WindowsByHandle
    for hwnd, proxy in WindowsByHandle.items():
        proxy._cleanup()
    WindowsByHandle = dict()