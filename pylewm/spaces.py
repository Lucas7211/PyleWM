import pylewm.window
import pylewm.layout
import pylewm.focus
from pylewm.commands import PyleCommand

import win32gui

@PyleCommand
def focus_left():
    focus_direction(pylewm.layout.Direction.Left)

@PyleCommand
def focus_right():
    focus_direction(pylewm.layout.Direction.Right)

@PyleCommand
def focus_up():
    focus_direction(pylewm.layout.Direction.Up)

@PyleCommand
def focus_down():
    focus_direction(pylewm.layout.Direction.Down)

@PyleCommand
def focus_next():
    focus_direction(pylewm.layout.Direction.Next)

@PyleCommand
def focus_previous():
    focus_direction(pylewm.layout.Direction.Previous)

def focus_direction(direction):
    current_space = get_focused_space()
    current_slot = current_space.get_last_focused_slot()
    new_slot, escape_direction = current_space.move_from_slot(current_slot, direction)

    if new_slot != -1:
        # Focus a different slot within this space
        pylewm.focus.set_focus(current_space.windows[new_slot])
    else:
        # Escape into a different monitor's space
        new_monitor = pylewm.monitors.get_monitor_in_direction(current_space.monitor, escape_direction)
        if new_monitor:
            new_slot, escape_direction = new_monitor.visible_space.move_from_slot(-1, escape_direction)
            if new_slot != -1:
                pylewm.focus.set_focus(new_monitor.visible_space.windows[new_slot])
            else:
                pylewm.focus.set_focus_monitor(new_monitor)


def get_cursor_position():
    return win32gui.GetCursorPos()

def get_cursor_space():
    monitor = pylewm.monitors.get_monitor_at(get_cursor_position())
    if not monitor:
        monitor = pylewm.monitors.get_default_monitor()
    return monitor.visible_space

def get_focused_space():
    if pylewm.focus.FocusWindow and pylewm.focus.FocusWindow.space and pylewm.focus.FocusWindow.space.visible:
        return pylewm.focus.FocusWindow.space
    return get_cursor_space()