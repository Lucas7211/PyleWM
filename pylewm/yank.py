from pylewm.commands import PyleCommand
import pylewm.window
import pylewm.focus

YankStack = []

@PyleCommand
def yank_window():
    window = pylewm.focus.FocusWindow
    if not window:
        return

    prev_space = None
    prev_focused = window.focused
    if window.space:
        prev_space = window.space
        window.space.remove_window(window)

    window.hide()

    if prev_focused:
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

    if pylewm.focus.FocusWindow:
        drop_slot, force_drop = space.get_drop_slot(
            pylewm.focus.FocusWindow.rect.center,
            pylewm.focus.FocusWindow.rect)
        space.add_window(window, at_slot=drop_slot)
    else:
        space.add_window(window)

    window.show()
    return window

@PyleCommand
def drop_window():
    window = drop_one_window()
    if window:
        pylewm.focus.set_focus(window)

@PyleCommand
def drop_all_windows():
    global YankStack

    focus_window = None
    for window in range(0, len(YankStack)):
        focus_window = drop_one_window()

    YankStack = []

    if focus_window:
        pylewm.focus.set_focus(focus_window)