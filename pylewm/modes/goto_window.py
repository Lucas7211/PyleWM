import pylewm
import pylewm.modes.list_mode

class WindowOption(pylewm.modes.list_mode.ListOption):
    def __init__(self, window):
        self.window = window
        self.name = self.window.window_title

    def confirm(self):
        pylewm.focus.set_focus(self.window)

@pylewm.commands.PyleCommand
def start_goto_window(hotkeys = {}):
    options = []

    for monitor in pylewm.monitors.Monitors:
        for space in monitor.spaces:
            for window in space.windows:
                options.append(WindowOption(window))

    pylewm.modes.list_mode.ListMode(hotkeys, options)()