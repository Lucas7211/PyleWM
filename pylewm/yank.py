from pylewm.commands import PyleCommand, PyleTask
import pylewm.monitors
import pylewm.window
import pylewm.focus
from pylewm.rects import Direction

YankStack : list[pylewm.window.Window] = []

@PyleCommand
def yank_window():
    window = pylewm.focus.FocusWindow
    if not window:
        return
    if window.is_ignored():
        return

    prev_space = None
    if window.space:
        prev_space = window.space
        window.space.remove_window(window)

    window.hide()

    if prev_space:
        pylewm.focus.set_focus_space(prev_space)
    else:
        pylewm.focus.set_focus_space(pylewm.focus.get_cursor_space())

    YankStack.append(window)

def drop_one_window():
    if not YankStack:
        return None

    space = pylewm.focus.get_focused_space()
    if not space:
        return None

    window = YankStack.pop()
    if window.is_tiled():
        if pylewm.focus.FocusWindow:
            drop_slot, force_drop = space.get_drop_slot(
                pylewm.focus.FocusWindow.real_position.center,
                pylewm.focus.FocusWindow.real_position)
            space.add_window(window, at_slot=drop_slot)
        else:
            space.add_window(window)
    else:
        prev_rect = window.real_position
        prev_monitor = pylewm.monitors.get_covering_monitor(prev_rect)
        new_monitor = space.monitor

        if prev_monitor != new_monitor:
            new_rect = prev_rect.for_relative_parent(prev_monitor.rect, new_monitor.rect)
            window.set_layout(new_rect, apply_margin=False)

    window.show()
    return window

@PyleCommand
def drop_window():
    window = drop_one_window()
    if window:
        pylewm.focus.set_focus(window)

@PyleTask(name="Drop All Yanked Windows")
@PyleCommand
def drop_all_windows():
    global YankStack

    space = pylewm.focus.get_focused_space()
    if not space:
        return

    focus_window = None
    for window in YankStack:
        if window.is_tiled():
            prev_monitor = pylewm.monitors.get_covering_monitor(window.real_position)
            relative_position = window.real_position.for_relative_parent(prev_monitor.rect, space.monitor.rect)

            drop_slot, force_drop = space.get_drop_slot(relative_position.center, relative_position)
            space.add_window(window, at_slot=drop_slot)
            window.show()
            focus_window = window
        else:
            prev_rect = window.real_position
            prev_monitor = pylewm.monitors.get_covering_monitor(prev_rect)
            new_monitor = space.monitor

            if not focus_window:
                focus_window = window

            if prev_monitor != new_monitor:
                new_rect = prev_rect.for_relative_parent(prev_monitor.rect, new_monitor.rect)
                window.set_layout(new_rect, apply_margin=False)

    YankStack = []

    if focus_window:
        pylewm.focus.set_focus(focus_window)

@PyleTask(name="Yank All Windows on Monitor")
@PyleCommand
def yank_all_windows_on_monitor():
    global YankStack

    space = pylewm.focus.get_focused_space()

    windows = list(space.windows)
    for window in windows:
        space.remove_window(window)
        window.hide()

    YankStack += windows
    pylewm.focus.set_focus_space(space)