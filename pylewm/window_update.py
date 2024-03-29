import pylewm.monitors
import pylewm.focus
import pylewm.filters
import pylewm.tabs
import time

from pylewm.window import Window, WindowsByProxy

HiddenFocusSpace = None
HiddenFocusSpaceSince = None

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

    # If the currently focused window is on a hidden space,
    # switch that monitor to the space the window is in.
    #  This can happen if some other application focuses it,
    #  for example clicking a link focusing the browser window
    #  from a different space.
    global HiddenFocusSpace
    global HiddenFocusSpaceSince
    if pylewm.focus.FocusWindow:
        space = pylewm.focus.FocusWindow.space
        if not space and pylewm.focus.FocusWindow.tab_group:
            space = pylewm.focus.FocusWindow.tab_group.visible_window.space
        if space and not space.visible:
            if space == HiddenFocusSpace:
                if (time.time() - HiddenFocusSpaceSince) > 0.05:
                    space.monitor.switch_to_space(space)
            else:
                HiddenFocusSpace = space
                HiddenFocusSpaceSince = time.time()
        else:
            HiddenFocusSpace = None
    else:
        HiddenFocusSpace = None

    # Update any registered update functions
    for update_func in WINDOW_UPDATE_FUNCS:
        update_func()

    # Update taskbar visibility if we have any
    update_taskbars()

    # Update any tab groups that need it
    pylewm.tabs.update_tabgroups()

WINDOW_UPDATE_FUNCS = []
def PyleWindowUpdate(func):
    WINDOW_UPDATE_FUNCS.append(func)
    return func

def window_initial_placement():
    """ Place windows detected during initial startup and place them correctly. """
    if not Window.InInitialPlacement:
        return

    windows = []

    # Update all windows so they have a chance to be placed into spaces
    for proxy, window in WindowsByProxy.items():
        window.update()
        if window.is_tiled():
            window.auto_place_into_space()

    Window.InInitialPlacement = False
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

def update_taskbars():
    i = len(Window.Taskbars) - 1
    should_hide = pylewm.config.HideTaskbar
    
    while i >= 0:
        window = Window.Taskbars[i]
        if window.closed:
            del Window.Taskbars[i]
        else:
            if should_hide:
                if not window.wm_hidden or window.window_info.visible:
                    window.hide()
            else:
                if window.wm_hidden:
                    window.show()
                    window.proxy.set_always_on_top(True)
        i -= 1