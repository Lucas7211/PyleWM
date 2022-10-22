from pylewm.commands import PyleCommand
from pylewm.rects import Rect
import pylewm.window
import pylewm.window_update
import pylewm.focus
import win32gui

DROPDOWN_WINDOW = None

@PyleCommand
def set_as_dropdown():
    window = pylewm.focus.FocusWindow
    if not window:
        return
    if window.is_ignored():
        return

    window.make_floating()
    window.hide()

    global DROPDOWN_WINDOW
    previous_window = DROPDOWN_WINDOW
    if previous_window:
        if previous_window.hidden:
            previous_window.is_dropdown = False
            previous_window.show()

    DROPDOWN_WINDOW = window
    window.is_dropdown = True

@PyleCommand
def toggle_dropdown():
    global DROPDOWN_WINDOW
    window = DROPDOWN_WINDOW

    if not window:
        return

    monitor = pylewm.focus.get_focused_monitor()

    width = monitor.rect.width / 2
    height = monitor.rect.height / 3

    dropdown_rect = Rect.from_pos_size(
        (monitor.rect.left + (monitor.rect.width - width) / 2, monitor.rect.top),
        (width, height),
    )

    if window.wm_hidden:
        window.show_with_rect(dropdown_rect)
        pylewm.focus.set_focus_no_mouse(window)
    else:
        window.hide()
    
@pylewm.window_update.PyleWindowUpdate
def update_dropdown():
    global DROPDOWN_WINDOW
    window = DROPDOWN_WINDOW

    if window:
        if window.closed:
            DROPDOWN_WINDOW = None
        if not window.wm_hidden:
            if not window.is_floating():
                window.is_dropdown = False
                DROPDOWN_WINDOW = None
            elif window != pylewm.focus.FocusWindow and not window.wm_becoming_visible:
                window.is_dropdown = True
                window.hide()