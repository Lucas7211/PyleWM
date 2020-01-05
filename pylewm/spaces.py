import pylewm.window
import pylewm.layout
import pylewm.focus
from pylewm.commands import PyleCommand, delay_pyle_command

import win32gui

def goto_space(other_space):
    other_space.monitor.switch_to_space(other_space)
    delay_pyle_command(0.05, lambda: pylewm.focus.set_focus_space(other_space))

@PyleCommand
def flip():
    space = pylewm.focus.get_focused_space()
    monitor = space.monitor

    other_space = None
    if space == monitor.spaces[0]:
        other_space = monitor.spaces[1]
    elif space == monitor.spaces[1]:
        other_space = monitor.spaces[0]
    elif monitor.last_used_space:
        other_space = monitor.last_used_space
    else:
        other_space = monitor.spaces[0]

    goto_space(other_space)

@PyleCommand
def goto_temporary():
    space = pylewm.focus.get_focused_space()
    monitor = space.monitor

    temp_space = None
    if space.temporary:
        # We want an -empty- temporary space now, since we are
        # already no a temporary space.
        temp_space = monitor.new_temp_space()
    elif len(monitor.temp_spaces) == 0:
        # Create the first temporary space
        temp_space = monitor.new_temp_space()
    else:
        # Switch to the last temporary space we had active
        temp_space = monitor.get_last_used_temp_space()

    goto_space(temp_space)

@PyleCommand
def next_temporary():
    space = pylewm.focus.get_focused_space()
    monitor = space.monitor
    if not space.temporary:
        return

    goto_space(monitor.get_adjacent_temp_space(space, +1))

@PyleCommand
def previous_temporary():
    space = pylewm.focus.get_focused_space()
    monitor = space.monitor
    if not space.temporary:
        return

    goto_space(monitor.get_adjacent_temp_space(space, -1))

@PyleCommand
def move_to_new_temporary_space():
    ''' Move the active window to a new temporary space. '''
    if not pylewm.focus.FocusWindow:
        return

    window = pylewm.focus.FocusWindow

    temp_space = window.space.monitor.new_temp_space()
    window.space.remove_window(window)
    temp_space.add_window(window)

    temp_space.monitor.switch_to_space(temp_space)
    delay_pyle_command(0.05, lambda: pylewm.focus.set_focus(window))

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
    current_space = pylewm.focus.get_focused_space()
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

@PyleCommand
def move_left():
    move_direction(pylewm.layout.Direction.Left)

@PyleCommand
def move_right():
    move_direction(pylewm.layout.Direction.Right)

@PyleCommand
def move_up():
    move_direction(pylewm.layout.Direction.Up)

@PyleCommand
def move_down():
    move_direction(pylewm.layout.Direction.Down)

@PyleCommand
def move_next():
    move_direction(pylewm.layout.Direction.Next)

@PyleCommand
def move_previous():
    move_direction(pylewm.layout.Direction.Previous)

def move_direction(direction):
    current_space = pylewm.focus.get_focused_space()
    current_slot = current_space.get_last_focused_slot()
    if current_slot == -1:
        return

    new_slot, escape_direction = current_space.move_from_slot(current_slot, direction)
    if new_slot != -1:
        # Swap window to a different slot
        current_space.swap_slots(current_slot, new_slot)
    else:
        # Escape into a different monitor's space
        new_monitor = pylewm.monitors.get_monitor_in_direction(current_space.monitor, escape_direction)
        if new_monitor:
            target_slot, target_direction = new_monitor.visible_space.move_from_slot(-1, escape_direction)

            focus_window = current_space.windows[current_slot]
            current_space.remove_window(focus_window)

            if target_slot != -1:
                new_monitor.visible_space.insert_slot(target_slot, escape_direction, focus_window)
            else:
                new_monitor.visible_space.add_window(focus_window)