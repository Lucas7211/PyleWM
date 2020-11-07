import pylewm.modes.overlay_mode
import pylewm

class ControlMouseMode(pylewm.modes.overlay_mode.OverlayMode):
    def __init__(self, hotkeys):
        super(ControlMouseMode, self).__init__(hotkeys)

        window = pylewm.focus.FocusWindow
        self.overlay_window(window)

@pylewm.commands.PyleCommand
def start_mouse_control(hotkeys):
    if not pylewm.focus.FocusWindow:
        return
    ControlMouseMode(hotkeys)()