from pylewm.commands import PyleCommand
from pylewm.rects import Rect
import pylewm.windows
import pylewm.window
import pylewm.focus
import win32gui

DROPDOWN_WINDOW = None

@PyleCommand
def set_as_dropdown():
    window = pylewm.focus.FocusWindow
    if not window:
        return

    window.make_floating()
    window.hide()

    global DROPDOWN_WINDOW
    previous_window = DROPDOWN_WINDOW
    if previous_window:
        if previous_window.hidden:
            previous_window.show()

    DROPDOWN_WINDOW = window

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

    if window.hidden:
        print("Show dropdown window at "+str(dropdown_rect))
        window.show_with_rect(dropdown_rect)
        pylewm.focus.set_focus_no_mouse(window)
    else:
        print("Hide dropdown window")
        window.hide()
    

@pylewm.windows.PyleWindowUpdate
def update_dropdown():
    global DROPDOWN_WINDOW
    window = DROPDOWN_WINDOW

    if window:
        if window.closed or not win32gui.IsWindow(window.handle):
            print("Dropdown window closed")
            DROPDOWN_WINDOW = None
        if not window.hidden:
            if not window.floating:
                print("Dropdown window placed into layout")
                DROPDOWN_WINDOW = None
            elif not window.focused and not window.becoming_visible:
                print("Lost focus on dropdown window")
                window.hide()