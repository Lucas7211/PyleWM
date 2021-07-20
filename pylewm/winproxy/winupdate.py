import functools

import pylewm.winproxy.winfuncs as winfuncs
from pylewm.winproxy.windowproxy import WindowProxy, WindowsByHandle, ProxyCommands
from pylewm.commands import CommandQueue, Commands
from pylewm.window import on_proxy_added, on_proxy_removed
from pylewm.winproxy.winfocus import update_focused_window

def proxy_update():
    """ In charge of updating all interactions with the win32 world. """

    # Update what windows are tracked
    detect_new_windows()

    # Update which window is currently focused
    update_focused_window()

    # Perform updates on tracked windows if we need to
    update_tracked_windows()

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