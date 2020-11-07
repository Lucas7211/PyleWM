import pylewm
import pylewm.modes.list_mode
import win32gui

class WindowOption(pylewm.modes.list_mode.ListOption):
    def __init__(self, window):
        self.window = window
        self.name = win32gui.GetWindowText(self.window.handle)

    def confirm(self):
        pylewm.focus.set_focus(self.window)

@pylewm.commands.PyleCommand
def start_goto_window(hotkeys = {}):
    options = []

    for hwnd, window in pylewm.windows.Windows.items():
        if win32gui.IsWindow(hwnd):
            options.append(WindowOption(window))

    pylewm.modes.list_mode.ListMode(hotkeys, options)()