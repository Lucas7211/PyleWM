import pylewm
import pylewm.hotkeys
import pylewm.execution
import pylewm.windows
import pylewm.monitors
import pylewm.tiles
import pylewm.scratch

import os

# Main modifier key that all the hotkeys are behind
MOD =                       'rctrl'

# Function to open a WSL command in a new wsltty window
@pylewm.pylecommand
def wsl_term(cmd=""):
    wsltty = r'%LOCALAPPDATA%\wsltty\bin\mintty.exe --wsl -h ' +\
               'err --configdir="%APPDATA%\wsltty" -o Locale=C -o ' +\
               'Charset=UTF-8 /bin/wslbridge -t /bin/bash'
    if cmd:
        wsltty += " -c \""+cmd+"\""
    return pylewm.execution.run(wsltty)()

# Turns a path from a windows path to the equivalent WSL path
def wsl_path(path):
    path = path.replace("\\", "/")
    path = path.replace(":/", "/")
    return "/mnt/" + path[0].lower() + path[1:]

HOTKEYS = {
    # Window focus control
    (MOD, 'h')              : pylewm.tiles.focus_dir("left"),
    (MOD, 'l')              : pylewm.tiles.focus_dir("right"),
    (MOD, 't')              : pylewm.tiles.focus_dir("down"),
    (MOD, 'n')              : pylewm.tiles.focus_dir("up"),
    (MOD, 's')              : pylewm.tiles.switch_next,
    (MOD, 'r')              : pylewm.tiles.switch_prev,

    # Floating layer
    (MOD, 'f')              : pylewm.tiles.toggle_floating,
    (MOD, 'lctrl', 'f')     : pylewm.floating.toggle_layer,
    (MOD, 'g')              : pylewm.tiles.focus_floating,

    # Window movement
    (MOD, 'shift', 'h')     : pylewm.tiles.move_dir("left"),
    (MOD, 'shift', 'l')     : pylewm.tiles.move_dir("right"),
    (MOD, 'shift', 't')     : pylewm.tiles.move_dir("down"),
    (MOD, 'shift', 'n')     : pylewm.tiles.move_dir("up"),

    # Virtual desktop management
    (MOD, 'w')              : pylewm.monitors.next_desktop,
    (MOD, 'v')              : pylewm.monitors.prev_desktop,
    (MOD, 'z')              : pylewm.monitors.new_desktop,

    # Yanking windows to scratch
    (MOD, 'y')              : pylewm.scratch.yank,
    (MOD, 'i')              : pylewm.scratch.drop,
    (MOD, 'shift', 'i')     : pylewm.scratch.drop_all,

    # Layout control
    (MOD, 'd')              : pylewm.tiles.vsplit,
    (MOD, 'b')              : pylewm.tiles.hsplit,
    (MOD, 'shift', 'd')     : pylewm.tiles.vextend,
    (MOD, 'shift', 'b')     : pylewm.tiles.hextend,
    (MOD, 'e')              : pylewm.tiles.extend,
    (MOD, 'm')              : pylewm.tiles.cancel_pending,

    # Window management
    (MOD, '$')              : pylewm.windows.close,
    (MOD, '/')              : pylewm.tiles.print_tree,

    # Application management
    (MOD, ';')              : wsl_term,
    (MOD, 'shift', ';')     : pylewm.execution.run(r'cmd.exe'),
    (MOD, ',')              : pylewm.execution.start_menu,
    (MOD, 'p')              : pylewm.execution.run(r'"C:\Program Files\qutebrowser\qutebrowser.exe"'),
    (MOD, 'k')              : wsl_term("ranger "+wsl_path(os.environ["USERPROFILE"])),
    (MOD, 'shift', 'k')     : pylewm.execution.run(r'explorer.exe'),
    (MOD, 'shift', 'r')     : pylewm.restart,
    (MOD, 'shift', 'q')     : pylewm.quit,
}

# Teleport the mouse to any window that focus has been switched to
pylewm.config["TeleportMouse"] = True

# Window classes to remove the titlebar of
pylewm.config["HideTitlebarWindows"] = [
    {"class": "mintty"},
    {"title": "qutebrowser"},
]

# Windows that should be completely ignored by the window manager
pylewm.config["IgnoreWindows"] = [
    {"title": "Windows Shell Experience Host"},
    {"title": "Store"},
]

# Windows that should always start floating
pylewm.config["FloatingWindows"] = [
]

# Windows that should always start tiling
pylewm.config["TilingWindows"] = [
    {"title": "*qutebrowser*", "class": "QT5QWindowIcon"},
]

if __name__ == "__main__":
    for key, val in HOTKEYS.items():
        pylewm.hotkeys.register(key, val)
    pylewm.start()
