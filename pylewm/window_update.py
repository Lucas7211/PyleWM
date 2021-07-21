import pylewm.monitors
import pylewm.focus
import pylewm.filters
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
        if time.time() > StartTime + 0.25:
            window_initial_placement()
            Window.InInitialPlacement = False


def window_initial_placement():
    """ Place windows detected during initial startup and place them correctly. """
    windows = []

    for monitor in pylewm.monitors.Monitors:
        for space in [*monitor.spaces, *monitor.temp_spaces]:
            handled = False
            if space.visible:
                handled = space.takeover_from_windows(space.initial_windows)

            if not handled:
                for window in space.initial_windows:
                    space.add_window(window)

            windows.extend(space.initial_windows)
            space.initial_windows = []

    for window in windows:
        pylewm.filters.trigger_all_filters(window, post=True)