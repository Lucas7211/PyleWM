from pylewm.commands import PyleCommand
from pylewm.window import Window, WindowState
import pylewm.winproxy.winfuncs as winfuncs

import time
import pylewm.focus
import pylewm.hotkeys
import pylewm.window_drag

@PyleCommand
def close():
    ''' Close the window that currently has focus. '''
    window = pylewm.focus.FocusWindow
    if window:
        space = window.space
        if space:
            space.remove_window(window)
            pylewm.focus.set_focus_space(space)
        window.close()

@PyleCommand
def drop_window_into_layout():
    ''' Drop a previously floating window into the layout of the monitor it's on. '''
    window = pylewm.focus.FocusWindow
    if not window:
        return
    if not window.is_floating():
        return

    window.make_tiled()
    window.auto_place_into_space()
    window.ignore_drag_until = time.time() + 0.1
    
@PyleCommand
def make_window_floating():
    window = pylewm.focus.FocusWindow
    if not window or not window.space:
        return

    window.make_floating()
    window.set_layout(window.floating_rect, apply_margin=False)
    window.can_drop_tiled = False

@PyleCommand
def toggle_window_floating():
    window = pylewm.focus.FocusWindow
    if window and window.is_tiled():
        make_window_floating().run()
    else:
        drop_window_into_layout().run()

@PyleCommand
def move_to_monitor(monitor_index):
    window = pylewm.focus.FocusWindow
    if not window:
        return
    window.ensure_tiled_for_move()
    if not window.space:
        return

    space = window.space
    monitor = pylewm.monitors.get_monitor_by_index(monitor_index)

    space.remove_window(window)
    monitor.visible_space.add_window(window)

@PyleCommand
def minimize():
    window = pylewm.focus.FocusWindow
    if not window:
        return

    window.minimize()

@PyleCommand
def vanish():
    window = pylewm.focus.FocusWindow
    if not window:
        return

    if window.space:
        window.space.remove_window(window)
    window.hide()

@PyleCommand
def poke():
    if pylewm.focus.FocusWindow:
        pylewm.focus.FocusWindow.poke()

@PyleCommand.Threaded
def show_window_info():
    window = pylewm.focus.FocusWindow
    if not window:
        state = "Unknown Window"
    else:
        state = f"""
Title: {window.window_title}
Class: {window.window_class}
State: {WindowState.name(window.state)}
Real Position: {window.real_position}
Layout Position: {window.layout_position}
"""

    winfuncs.ShowMessageBox("PyleWM: Window Info", state)