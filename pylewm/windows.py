import pylewm.monitors
import pylewm.focus
import time

from pylewm.window import Window, WindowsByProxy

StartTime = time.time()

def window_update():
    # Update spaces on all monitors
    for monitor in pylewm.monitors.Monitors:
        for space in monitor.spaces:
            space.update_layout(pylewm.focus.FocusWindow)
        for space in monitor.temp_spaces:
            space.update_layout(pylewm.focus.FocusWindow)

    # Update all windows
    for proxy, window in WindowsByProxy.items():
        window.update()

    # Once we've been running for one second we are no longer in initial placement mode
    if Window.InInitialPlacement:
        if time.time() > StartTime + 1.0:
            Window.InInitialPlacement = False