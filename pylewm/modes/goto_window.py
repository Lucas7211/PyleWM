import pylewm
import pylewm.modes.list_mode
from pylewm.window import WindowsByProxy, WindowState

class WindowOption(pylewm.modes.list_mode.ListOption):
    def __init__(self, window):
        self.window = window
        self.name = self.window.window_title

        if window.window_info.is_minimized():
            self.detail = "(Minimized)"

    def confirm(self):
        if self.window.window_info.is_minimized():
            self.window.restore()
        pylewm.focus.set_focus(self.window)

@pylewm.commands.PyleCommand
def start_goto_window(hotkeys = {}):

    options = []
    for proxy, window in WindowsByProxy.items():
        if window.closed:
            continue
        if window.state == WindowState.IgnorePermanent:
            continue
        if window.is_taskbar:
            continue
        if window.window_info.cloaked:
            continue
        if window.window_title == "":
            continue
        if window.real_position.height == 0 or window.real_position.width == 0:
            continue
        if not window.space:
            if not window.window_info.visible and not window.window_info.is_minimized():
                continue
        if window.is_dropdown:
            continue
        option = WindowOption(window)
        options.append(option)

    mode = pylewm.modes.list_mode.ListMode(hotkeys, options)
    mode()