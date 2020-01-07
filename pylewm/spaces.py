import pylewm.window
import pylewm.layout
import pylewm.focus
from pylewm.commands import PyleCommand, delay_pyle_command

import win32gui

def goto_space(other_space):
    other_space.monitor.switch_to_space(other_space)

    if other_space.last_focus:
        focus_window = other_space.last_focus
        delay_pyle_command(0.05, lambda: pylewm.focus.set_focus(focus_window))
    elif other_space.windows:
        focus_window = other_space.windows[0]
        delay_pyle_command(0.05, lambda: pylewm.focus.set_focus(focus_window))
    else:
        delay_pyle_command(0.05, lambda: pylewm.focus.set_focus_monitor(other_space.monitor))

def get_flipped_space():
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

    return other_space

@PyleCommand
def flip():
    goto_space(get_flipped_space())

@PyleCommand
def move_flip():
    window = pylewm.focus.FocusWindow
    if not window:
        return
    if not window.can_move():
        return

    space = get_flipped_space()
    if window.space:
        window.space.remove_window(window)
        space.add_window(window)

    space.monitor.switch_to_space(space)

@PyleCommand
def focus_space(monitor_index, space_index):
    monitor = pylewm.monitors.get_monitor_by_index(monitor_index)
    space = monitor.spaces[space_index]

    if space.visible:
        pylewm.focus.set_focus_space(space)
    else:
        goto_space(space)

@PyleCommand
def move_to_space(monitor_index, space_index):
    window = pylewm.focus.FocusWindow
    if not window or not window.space:
        return
    if not window.can_move():
        return

    prev_space = window.space
    prev_space.remove_window(window)

    monitor = pylewm.monitors.get_monitor_by_index(monitor_index)
    space = monitor.spaces[space_index]
    space.add_window(window)

    if not space.visible:
        space.monitor.switch_to_space(space)

@PyleCommand
def goto_temporary():
    space = pylewm.focus.get_focused_space()
    monitor = space.monitor

    temp_space = None
    if space.temporary and space.windows:
        # We want an -empty- temporary space now, since we are
        # already on a non-empty temporary space.
        temp_space = monitor.new_temp_space()
    elif len(monitor.temp_spaces) == 0:
        # Create the first temporary space
        temp_space = monitor.new_temp_space()
    else:
        # Switch to the last temporary space we had active
        temp_space = monitor.get_last_used_temp_space()
        monitor.set_primary_temp_space(temp_space)

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
    if not pylewm.focus.FocusWindow.can_move():
        return
    if not pylewm.focus.FocusWindow.space:
        return
    move_window_to_new_temporary_space(pylewm.focus.FocusWindow)
    delay_pyle_command(0.05, lambda: pylewm.focus.set_focus(pylewm.focus.FocusWindow))

def move_window_to_new_temporary_space(window):
    temp_space = window.space.monitor.new_temp_space()
    window.space.remove_window(window)
    temp_space.add_window(window)

    temp_space.monitor.switch_to_space(temp_space)

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
    current_window = current_space.get_last_focus()

    new_window, escape_direction = current_space.get_window_in_direction(current_window, direction)

    if new_window:
        # Focus a different slot within this space
        pylewm.focus.set_focus(new_window)
    else:
        # Escape into a different monitor's space
        new_monitor = pylewm.monitors.get_monitor_in_direction(current_space.monitor, escape_direction)
        if new_monitor:
            new_window, escape_direction = new_monitor.visible_space.get_window_in_direction(None, escape_direction)
            if new_window:
                pylewm.focus.set_focus(new_window)
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
    focus_window = pylewm.focus.FocusWindow
    if not focus_window or focus_window.space != current_space:
        return
    if not focus_window.can_move():
        return

    handled, escape_direction = current_space.move_window_in_direction(focus_window, direction)
    if not handled:
        # Escape into a different monitor's space
        new_monitor = pylewm.monitors.get_monitor_in_direction(current_space.monitor, escape_direction)
        if new_monitor:
            current_space.remove_window(focus_window)
            new_monitor.visible_space.add_window(focus_window, direction=escape_direction)

@PyleCommand
def next_layout():
    current_space = pylewm.focus.get_focused_space()
    if current_space:
        current_space.switch_layout(+1)

@PyleCommand
def previous_layout():
    current_space = pylewm.focus.get_focused_space()
    if current_space:
        current_space.switch_layout(-1)

@PyleCommand
def show_spaces_info():
    text = ""
    for monitor_index, monitor in enumerate(pylewm.monitors.Monitors):
        text += f"Monitor {monitor_index} at {monitor.rect}\n"
        text += f"===================\n"
        for i, space in enumerate(monitor.spaces):
            text += f"[ Space {i} (Visible: {space.visible}) ]\n"
            text += f"-------------------\n"
            for window in space.windows:
                text += f"{window.window_title}\n"
            text += f"\n"
        for i, space in enumerate(monitor.temp_spaces):
            text += f"[ Temp Space {i} (Visible: {space.visible}) ]\n"
            text += f"-------------------\n"
            for window in space.windows:
                text += f"* {window.window_title}\n"
            text += f"\n"
        text += "\n\n"

    import ctypes
    ctypes.windll.user32.MessageBoxW(None, text, 'PyleWM: Spaces Info', 0)