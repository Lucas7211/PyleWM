from pylewm.commands import PyleCommand
from pylewm.rects import Rect
import pylewm.window
import pylewm.execution
import pylewm.window_update
import pylewm.monitors
import pylewm.window
import pylewm.focus
import time
import win32gui

ZOOMED_WINDOW : pylewm.window.Window = None
ZOOM_PREVIOUS_POSITION = None
ZOOM_FULL_POSITION = None

@PyleCommand
def toggle_zoomed():
    """
        Temporarily expand a window to the full size of the monitor it is on.
        When the window loses focus, it will go back to its previous position.
    """

    global ZOOMED_WINDOW
    global ZOOM_PREVIOUS_POSITION
    global ZOOM_FULL_POSITION

    window = pylewm.focus.FocusWindow
    if not window:
        return

    if window.is_zoomed:
        if window.is_floating() and ZOOM_PREVIOUS_POSITION:
            window.move_floating_to(ZOOM_PREVIOUS_POSITION)
        window.is_zoomed = False
        window.refresh_layout()
        pylewm.focus.set_focus(window)
        ZOOMED_WINDOW = None
    else:
        window.is_zoomed = True
        ZOOMED_WINDOW = window
        ZOOM_PREVIOUS_POSITION = window.real_position.copy()

        window.proxy.set_always_on_top(True)

        monitor : pylewm.monitors.Monitor = None
        if window.space and window.space.monitor:
            monitor = window.space.monitor
        else:
            monitor = pylewm.monitors.get_covering_monitor(window.real_position)
            if not monitor:
                monitor = pylewm.monitors.get_monitor_by_index(0)

        ZOOM_FULL_POSITION = monitor.rect.padded(10, 10)
        if window.tab_group:
            ZOOM_FULL_POSITION.top += 30

        if window.is_tiled():
            window.proxy.set_layout(ZOOM_FULL_POSITION, False)
        else:
            window.move_floating_to(ZOOM_FULL_POSITION)

        pylewm.focus.set_focus(window)

@pylewm.window_update.PyleWindowUpdate
def update_zoomed():
    global ZOOMED_WINDOW
    global ZOOM_FULL_POSITION
    global ZOOM_PREVIOUS_POSITION
    window = ZOOMED_WINDOW

    if window:
        if window.closed:
            ZOOMED_WINDOW = None
        if window != pylewm.focus.FocusWindow and not window.wm_becoming_visible:
            if (pylewm.focus.FocusWindow
                and window.tab_group
                and pylewm.focus.FocusWindow.tab_group == window.tab_group
                ):

                window.is_zoomed = False
                if window.is_tiled():
                    window.proxy.set_always_on_top(False)
                window.refresh_layout()

                ZOOMED_WINDOW = pylewm.focus.FocusWindow
                ZOOMED_WINDOW.is_zoomed = True
                ZOOM_PREVIOUS_POSITION = ZOOMED_WINDOW.real_position.copy()

                ZOOMED_WINDOW.proxy.set_always_on_top(True)
                if ZOOMED_WINDOW.is_tiled():
                    ZOOMED_WINDOW.proxy.set_layout(ZOOM_FULL_POSITION, False)
                else:
                    ZOOMED_WINDOW.move_floating_to(ZOOM_FULL_POSITION)
            else:
                window.is_zoomed = False
                if window.is_tiled():
                    window.proxy.set_always_on_top(False)
                window.refresh_layout()
                ZOOMED_WINDOW = None
        elif not window.is_zoomed or window.wm_hidden or (not window.real_position.equals(ZOOM_FULL_POSITION) and not window.real_position.equals(ZOOM_PREVIOUS_POSITION)):
            window.is_zoomed = False
            window.refresh_layout()
            ZOOMED_WINDOW = None