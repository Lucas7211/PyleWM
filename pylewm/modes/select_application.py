import pylewm
import pylewm.modes.list_mode
import win32gui
import os
import pylnk3
from win32com.shell import shell, shellcon

class ApplicationOption(pylewm.modes.list_mode.ListOption):
    def __init__(self, path):
        self.path = path
        self.name = os.path.splitext(os.path.basename(self.path))[0]

    def confirm(self):
        pylewm.hotkeys.queue_command(pylewm.execution.run(["cmd.exe", "/C", self.path]))

STARTMENU_ITEMS = []
def get_startmenu_items():
    global STARTMENU_ITEMS
    if STARTMENU_ITEMS:
        return STARTMENU_ITEMS

    folders = [
        shell.SHGetFolderPath(0, shellcon.CSIDL_COMMON_STARTMENU, 0, 0),
        shell.SHGetFolderPath(0, shellcon.CSIDL_STARTMENU, 0, 0),
        shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, 0, 0),
        shell.SHGetFolderPath(0, shellcon.CSIDL_COMMON_DESKTOPDIRECTORY, 0, 0),
    ]

    STARTMENU_ITEMS = []
    existing_items = set()
    for folder in folders:
        for root, dirs, files in os.walk(folder):
            for name in files:
                if name.endswith(".lnk"):
                    option = ApplicationOption(os.path.join(root, name))
                    if option.name not in existing_items:
                        STARTMENU_ITEMS.append(option)
                        existing_items.add(option.name)

    return STARTMENU_ITEMS

@pylewm.commands.PyleCommand
def run_application(hotkeys = {}):
    mode = pylewm.modes.list_mode.ListMode(hotkeys, get_startmenu_items())
    mode.bg_selected_color = (160, 80, 0)
    mode()