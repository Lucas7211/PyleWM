import functools
import win32con
import collections
import time

import pylewm.hotkeys
import pylewm.winproxy.winfuncs as winfuncs
from pylewm.winproxy.windowproxy import WindowProxy, WindowsByHandle, ProxyCommands, InteractiveWindowProxies
from pylewm.commands import CommandQueue, Commands
from pylewm.window import Window, on_proxy_added, on_proxy_removed
from pylewm.winproxy.winfocus import update_focused_window
from pylewm.window_update import window_initial_placement

StartTime = None
LastInteractiveUpdateDuration = 0
LastBackgroundUpdateDuration = 0
LastTotalUpdateDuration = 0
DetectedInitialWindows = False

BackgroundWindowProxies_Active = collections.deque()
BackgroundWindowProxies_Queued = collections.deque()

def proxy_update():
    """ In charge of updating all interactions with the win32 world. """
    global LastTotalUpdateDuration
    global DetectedInitialWindows

    # Record when we started updating
    global StartTime
    if StartTime is None:
        StartTime = time.time()

    start_time = time.perf_counter()

    # Update what windows are tracked
    if not DetectedInitialWindows:
        detect_existing_windows()
        def proxy_detect_window(hwnd):
            ProxyCommands.queue(lambda: detect_window(hwnd))
        pylewm.hotkeys.window_creation_function = proxy_detect_window
        DetectedInitialWindows = True

    # Update which window is currently focused
    update_focused_window()

    # Perform updates on tracked windows if we need to
    update_tracked_windows()

    # Update global state in the application
    update_global_state()

    LastTotalUpdateDuration = time.perf_counter() - start_time

def detect_window(hwnd):
    if hwnd in WindowsByHandle:
        return
    if WindowProxy._should_skip_detect_hwnd(hwnd):
        return
    window = WindowProxy(hwnd)
    WindowsByHandle[hwnd] = window
    InteractiveWindowProxies.add(window)

    if not window.initialized:
        window._initialize()
        Commands.queue(functools.partial(on_proxy_added, window))
    window._update()

def detect_existing_windows():
    """ Detect any newly created windows that we aren't tracking. """
    new_windows = []
    def enum_window(hwnd, lparam):
        new_windows.append(hwnd)
        return True
    winfuncs.EnumWindows(winfuncs.tEnumWindowFunc(enum_window), 0)

    for hwnd in new_windows:
        detect_window(hwnd)

def update_tracked_windows():
    """ Perform update logic for all windows that are currently tracked. """
    global BackgroundWindowProxies_Active
    global BackgroundWindowProxies_Queued
    global LastInteractiveUpdateDuration
    global LastBackgroundUpdateDuration
    global LastTotalUpdateDuration

    start_time = time.perf_counter()
    WindowProxy.UpdateFrameCounter += 1
    WindowProxy.UpdateStartTime = time.time()

    invalid_windows = []
    reclassify_windows = []

    for window in InteractiveWindowProxies:
        if window.valid:
            if not window.initialized:
                window._initialize()
                Commands.queue(functools.partial(on_proxy_added, window))
            window._update()

            if window.is_background_update():
                reclassify_windows.append(window)
        if not window.valid:
            invalid_windows.append(window)

    interactive_end_time = time.perf_counter()
    LastInteractiveUpdateDuration = interactive_end_time - start_time

    # Update some background windows
    global BackgroundWindowProxies_Active
    global BackgroundWindowProxies_Queued

    background_count = len(BackgroundWindowProxies_Active) + len(BackgroundWindowProxies_Queued)
    update_count = min(max(background_count // 60, 10), background_count)
    update_index = 0

    while update_index < update_count:
        if len(BackgroundWindowProxies_Active) == 0:
            active_list = BackgroundWindowProxies_Active
            BackgroundWindowProxies_Active = BackgroundWindowProxies_Queued
            BackgroundWindowProxies_Queued = active_list

            if len(BackgroundWindowProxies_Active) == 0:
                break

        window = BackgroundWindowProxies_Active.popleft()
        if window.valid:
            if not window.initialized:
                window._initialize()
                Commands.queue(functools.partial(on_proxy_added, window))
            window._update()
            if window.is_background_update():
                BackgroundWindowProxies_Queued.append(window)
            else:
                InteractiveWindowProxies.add(window)
        if not window.valid:
            invalid_windows.append(window)

        update_index += 1

    LastBackgroundUpdateDuration = time.perf_counter() - interactive_end_time

    # Reclassify windows from interactive to background
    for window in reclassify_windows:
        if window in InteractiveWindowProxies:
            InteractiveWindowProxies.remove(window)
        BackgroundWindowProxies_Queued.append(window)

    # Cleanup invalid windows
    for window in invalid_windows:
        if window._hwnd not in WindowsByHandle:
            continue
        del WindowsByHandle[window._hwnd]
        if window in InteractiveWindowProxies:
            InteractiveWindowProxies.remove(window)
        Commands.queue(functools.partial(on_proxy_removed, window))

def update_global_state():
    # Window needs to know if left mouse button is down
    Window.IsLeftMouseHeld = (winfuncs.GetAsyncKeyState(win32con.VK_LBUTTON) != 0)

    # Trigger initial placement after our window proxies settle down
    if Window.InInitialPlacement and (time.time() - StartTime) > 0.2:
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