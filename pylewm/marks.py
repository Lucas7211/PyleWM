import pylewm
import pylewm.focus
import pylewm.hotkeys
import pylewm.desktops

import win32gui, win32con

Marks = []

@pylewm.pylecommand
def mark_window(mark=None):
    """ Mark the focused window with a particular mark. """
    if mark is None:
        # The next key pressed is the mark key
        print("Prompt for mark_window mark")
        pylewm.hotkeys.prompt_key(do_mark_window)
        return

    do_mark_window(pylewm.hotkeys.KeySpec.fromTuple((mark)))

def do_mark_window(keyspec):
    for mark in Marks:
        if mark[0] == keyspec:
            Marks.remove(mark)
            break

    window = win32gui.GetForegroundWindow()
    if win32gui.IsWindow(window):
        title = win32gui.GetWindowText(window)
        print(f"Mark window {title} with mark {keyspec}")
        Marks.append((keyspec, window, title))

@pylewm.pylecommand
def goto_window(mark=None):
    """ Focus the window with a particular mark. """
    if mark is None:
        # The next key pressed is the mark key
        print("Prompt for goto_window mark")
        pylewm.hotkeys.prompt_key(do_goto_window)
        return

    do_goto_window(pylewm.hotkeys.KeySpec.fromTuple((mark)))

def do_goto_window(keyspec):
    for mark in Marks:
        if mark[0] == keyspec:
            if win32gui.IsWindow(mark[1]):
                # Focus the marked window
                print(f"Goto window {win32gui.GetWindowText(mark[1])} with mark {keyspec}")
                do_focus(mark[1])
            else:
                # See if there's a window with the same name
                window = win32gui.FindWindow(None, mark[2])
                if win32gui.IsWindow(window):
                    print(f"Goto found window {win32gui.GetWindowText(mark[2])} with mark {keyspec}")
                    do_focus(window)

                    Marks.append((mark[0], window, mark[1]))
                    Marks.remove(mark)
            return

def do_focus(window):
    pylewm.desktops.switch_to_containing(window)
    pylewm.focus.set(window)
