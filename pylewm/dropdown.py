from pylewm.commands import PyleCommand
from pylewm.rects import Rect
import pylewm.window
import pylewm.execution
import pylewm.window_update
import pylewm.window
import pylewm.focus
import time
import win32gui

DROPDOWN_WINDOW = None
DROPDOWN_SHOW_TIME = 0.0

@PyleCommand
def set_as_dropdown():
    window = pylewm.focus.FocusWindow
    if not window:
        return
    if window.is_ignored():
        return

    make_window_dropdown(window)

def make_window_dropdown(window):
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
def toggle_dropdown(command_if_no_dropdown=None):
    global DROPDOWN_WINDOW
    window = DROPDOWN_WINDOW

    if window:
        if window.wm_hidden:
            pylewm.commands.run_pyle_command(show_dropdown)
        else:
            pylewm.commands.run_pyle_command(hide_dropdown)
    elif command_if_no_dropdown:
        pylewm.commands.run_pyle_command(pylewm.execution.run(command_if_no_dropdown))

        def make_next_window_dropdown(window):
            make_window_dropdown(window)
            pylewm.commands.run_pyle_command(show_dropdown)
            pylewm.commands.delay_pyle_command(0.2, lambda: window.poke())

        pylewm.window.execute_on_next_window(make_next_window_dropdown)

@PyleCommand
def show_dropdown():
    global DROPDOWN_WINDOW
    global DROPDOWN_SHOW_TIME
    window = DROPDOWN_WINDOW

    if window:
        monitor = pylewm.focus.get_focused_monitor()

        width = monitor.rect.width / 2
        height = monitor.rect.height / 3

        dropdown_rect = Rect.from_pos_size(
            (monitor.rect.left + (monitor.rect.width - width) / 2, monitor.rect.top),
            (width, height),
        )
        
        DROPDOWN_SHOW_TIME = time.time()
        window.show_with_rect(dropdown_rect)
        pylewm.focus.set_focus_no_mouse(window)
        
@PyleCommand
def hide_dropdown():
    global DROPDOWN_WINDOW
    window = DROPDOWN_WINDOW

    if window:
        window.hide()
    
@pylewm.window_update.PyleWindowUpdate
def update_dropdown():
    global DROPDOWN_WINDOW
    global DROPDOWN_SHOW_TIME
    window = DROPDOWN_WINDOW

    if window:
        if window.closed:
            DROPDOWN_WINDOW = None
        if not window.wm_hidden:
            if not window.is_floating():
                window.is_dropdown = False
                DROPDOWN_WINDOW = None
            elif window != pylewm.focus.FocusWindow and not window.wm_becoming_visible and time.time() > DROPDOWN_SHOW_TIME + 1.0:
                window.is_dropdown = True
                window.hide()