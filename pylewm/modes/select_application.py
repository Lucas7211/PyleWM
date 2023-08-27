import pylewm
import pylewm.modes.list_mode
import win32gui
import os

from win32com.shell import shell, shellcon

class ApplicationOption(pylewm.modes.list_mode.ListOption):
    def __init__(self, path):
        self.path = path
        self.name = os.path.splitext(os.path.basename(self.path))[0]

    def confirm(self):
        pylewm.hotkeys.queue_command(pylewm.execution.run(["cmd.exe", "/C", self.path]))

class SettingsOption(pylewm.modes.list_mode.ListOption):
    def __init__(self, name, command):
        self.command = command
        self.name = name

    def confirm(self):
        pylewm.hotkeys.queue_command(pylewm.execution.run_shell(["cmd.exe", "/C", "start", self.command]))

SETTINGS_PAGES = {
    "Windows Settings": "ms-settings:",
    "Display Settings": "ms-settings:display",
    "Night light settings": "ms-settings:nightlight",
    "Advanced scaling settings": "ms-settings:display-advanced",
    "Graphics settings": "ms-settings:display-advancedgraphics",
    "Display orientation settings": "ms-settings:screenrotation",
    "Sound settings": "ms-settings:sound",
    "Manage sound devices": "ms-settings:sound-devices",
    "App volume and device preferences": "ms-settings:apps-volume",
    "Notifications & actions settings": "ms-settings:notifications",
    "Focus assist settings": "ms-settings:quiethours",
    "Power & sleep settings": "ms-settings:powersleep",
    "Battery settings": "ms-settings:battery",
    "Battery usage details": "ms-settings:batterysaver-usagedetails",
    "Battery saver settings": "ms-settings:batterysaver-settings",
    "Storage settings": "ms-settings:storagesense",
    "Configure Storage Sense": "ms-settings:storagepolicies",
    "Save locations settings": "ms-settings:savelocations",
    "Tablet mode settings": "ms-settings:tabletmode",
    "Multitasking settings": "ms-settings:multitasking",
    "Projecting this PC": "ms-settings:project",
    "Shared experiences settings": "ms-settings:crossdevice",
    "Clipboard settings": "ms-settings:clipboard",
    "Remote Desktop settings": "ms-settings:remotedesktop",
    "Device Encryption settings": "ms-settings:deviceencryption",
    "About settings": "ms-settings:about",
    "Bluetooth & other devices": "ms-settings:bluetooth",
    "Printers & Scanners": "ms-settings:printers",
    "Mouse settings": "ms-settings:mousetouchpad",
    "Touchpad settings": "ms-settings:devices-touchpad",
    "Typing settings": "ms-settings:typing",
    "Pen & Windows ink settings": "ms-settings:pen",
    "AutoPlay settings": "ms-settings:autoplay",
    "USB settings": "ms-settings:usb",
    "Phone settings": "ms-settings:mobile-devices",
    "Network & Internet settings": "ms-settings:network",
    "Network status": "ms-settings:network-status",
    "Show available networks": "ms-availablenetworks:",
    "Wi-Fi settings": "ms-settings:network-wifi",
    "Personalization settings": "ms-settings:personalization",
    "Taskbar settings": "ms-settings:taskbar",
    "Apps & features": "ms-settings:appsfeatures",
    "Manage optional features": "ms-settings:optionalfeatures",
    "Default apps settings": "ms-settings:defaultapps",
    "Startup apps settings": "ms-settings:startupapps",
    "Date & time settings": "ms-settings:dateandtime",
    "Region settings": "ms-settings:regionformatting",
    "Language settings": "ms-settings:regionlanguage",
    "Windows update": "ms-settings:windowsupdate",
    "Windows defender": "windowsdefender:",
}

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
                if name.endswith(".lnk") or name.endswith(".bat") or name.endswith(".exe"):
                    option = ApplicationOption(os.path.join(root, name))
                    if option.name not in existing_items:
                        STARTMENU_ITEMS.append(option)
                        existing_items.add(option.name)

    for name, command in SETTINGS_PAGES.items():
        option = SettingsOption(name, command)
        STARTMENU_ITEMS.append(option)

    return STARTMENU_ITEMS

@pylewm.commands.PyleCommand
def run_application(hotkeys = {}):
    mode = pylewm.modes.list_mode.ListMode(hotkeys, get_startmenu_items())
    mode.bg_selected_color = (160, 80, 0)
    mode()