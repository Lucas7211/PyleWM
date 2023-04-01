import pylewm
import pylewm.modes.list_mode
from pylewm.window import WindowsByProxy, WindowState

from pylewm.winproxy.winfuncs import IsWindow

class WindowOption(pylewm.modes.list_mode.ListOption):
    def __init__(self, window):
        self.window = window
        self.name = self.window.window_title

    def confirm(self):
        if self.window.window_info.is_minimized():
            self.window.restore()
        self.window.show()
        pylewm.focus.set_focus(self.window)

@pylewm.commands.PyleTask(name="Retrieve Hidden Window")
@pylewm.commands.PyleCommand
def start_retrieve_hidden_window(hotkeys = {}):
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
        if window.space:
            continue
        if window.window_info.visible:
            continue
        if window.is_dropdown:
            continue
        if not IsWindow(window.proxy._hwnd):
            continue

        option = WindowOption(window)
        options.append(option)

    mode = pylewm.modes.list_mode.ListMode(hotkeys, options)
    mode()

@pylewm.commands.PyleTask(name="Permanently Hide Window")
@pylewm.commands.PyleCommand
def permanently_hide_window():
    window = pylewm.focus.FocusWindow
    if window:
        window.proxy.hide_permanent()
        if window.space:
            window.space.remove_window(window)