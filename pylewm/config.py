import pylewm.hotkeys
from pylewm.commands import PyleCommand

import os
import sys
import shutil

# Whether to allow dropping windows into a layout by drag and drop
AllowDroppingIntoLayout = True

# Whether the taskbar should be hidden completely while PyleWM is active
HideTaskbar = False

# The margin between windows tiled on the same monitor
TilingInnerMargin = 0
# The margin between a window and the edge of the monitor
TilingOuterMargin = [0, 0, 0, 1]

# Whitelisted window classes that can use "responsive placement mode", to tile them
# before they become visible to improve the responsiveness of window management
WHITELIST_INTERACTIBLE_CLASSES = [
    "CASCADIA_HOSTING_WINDOW_CLASS",
    "MozillaWindowClass",
    "CabinetWClass",
]

CONFIG_HOTKEYS = {}
CONFIG_FILTERS = []

def apply_default_config():
    import pylewm.pylewm_default_config
    pylewm.pylewm_default_config.apply()

def hotkeys(added_hotkeys):
    global CONFIG_HOTKEYS
    for key, val in added_hotkeys.items():
        CONFIG_HOTKEYS[key] = val

def filters(added_filters):
    global CONFIG_FILTERS
    CONFIG_FILTERS += added_filters

def get_config_dir():
    return os.path.expandvars(r"%APPDATA%\PyleWM")

def apply():
    config_dir = get_config_dir()
    config_file = os.path.join(config_dir, "PyleWM_Config.py")

    # Create config folder if one doesn't exist
    if not os.path.isdir(config_dir):
        os.makedirs(config_dir)

    # Copy default config if one doesn't exist
    if not os.path.isfile(config_file):
        pkg_dir = os.path.dirname(__file__)
        example_file = os.path.join(pkg_dir, "pylewm_example_config.py")
        if os.path.isfile(example_file):
            shutil.copy2(example_file, config_file)

    if os.path.isfile(config_file):
        # Import config from configuration directory
        import importlib.util

        config_spec = importlib.util.spec_from_file_location("pylewm_config", config_file)
        config_module = importlib.util.module_from_spec(config_spec)

        config_spec.loader.exec_module(config_module)
    else:
        # Fallback to the default config
        apply_default_config()

    # Firefox draws on its window borders so we need to space it out to prevent overlapping
    DEFAULT_FILTERS = [
        ({"class": "MozillaWindowClass"}, pylewm.filters.ForceBorders([2, 0, 2, 2])),
    ]

    for key, val in CONFIG_HOTKEYS.items():
        if val:
            pylewm.hotkeys.register(key, val)
    pylewm.filters.Filters = DEFAULT_FILTERS+CONFIG_FILTERS