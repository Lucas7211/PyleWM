import pylewm
import pylewm.modes.list_mode
import win32gui, win32con

class WindowOption(pylewm.modes.list_mode.ListOption):
    def __init__(self, window):
        self.window = window
        self.name = win32gui.GetWindowText(self.window.handle)

    def confirm(self):
        if self.window.minimized:
            self.window.take_new_rect = True
            win32gui.ShowWindow(self.window.handle, win32con.SW_RESTORE)
        pylewm.focus.set_focus(self.window)

@pylewm.commands.PyleCommand
def start_goto_window(hotkeys = {}):

    options = []
    for hwnd, window in pylewm.windows.Windows.items():
        if win32gui.IsWindow(hwnd):
            option = WindowOption(window)
            options.append(option)

    pylewm.modes.list_mode.ListMode(hotkeys, options)()