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
            plyewm.focus.set_focus_space(pylewm.focus.get_cursor_space())

    YankStack.append(window)

@PyleCommand
def drop_window():
    if not YankStack:
        return

    space = pylewm.focus.get_focused_space()
    if not space:
        return

    window = YankStack.pop()

    if pylewm.focus.FocusWindow:
        drop_slot, force_drop = space.get_drop_slot(
            pylewm.focus.FocusWindow.rect.center,
            pylewm.focus.FocusWindow.rect)
        space.drop_into_slot(window, drop_slot)
    else:
        space.add_window(window)

    window.show()
    pylewm.focus.set_focus(window)