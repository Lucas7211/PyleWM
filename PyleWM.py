import pylewm
import pylewm.hotkeys
import pylewm.execution
import pylewm.windows
import pylewm.desktops
import pylewm.tiles
import pylewm.scratch
import pylewm.marks
from pylewm.filters import *

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
    (MOD, 'shift', 'g')     : pylewm.floating.focus_next,
    (MOD, 'lctrl', 'g')     : pylewm.floating.focus_prev,

    # Floating window movement mode
    (MOD, 'c')              : pylewm.floating.if_floating(
        pylewm.hotkeys.Mode({
            ('h')            : pylewm.floating.move_dir("left"),
            ('l')            : pylewm.floating.move_dir("right"),
            ('j')            : pylewm.floating.move_dir("down"),
            ('k')            : pylewm.floating.move_dir("up"),
            ('shift', 'h')   : pylewm.floating.shrink_dir("right"),
            ('shift', 'l')   : pylewm.floating.grow_dir("right"),
            ('shift', 'j')   : pylewm.floating.grow_dir("down"),
            ('shift', 'k')   : pylewm.floating.shrink_dir("down"),
            ('t')            : pylewm.floating.center,
            ('q')            : pylewm.hotkeys.escape_mode,
        })
    ),

    # Move floating windows between monitors
    (MOD, 'alt', 'h')       : pylewm.floating.move_dir_monitor("left"),
    (MOD, 'alt', 'l')       : pylewm.floating.move_dir_monitor("right"),
    (MOD, 'alt', 't')       : pylewm.floating.move_dir_monitor("down"),
    (MOD, 'alt', 'n')       : pylewm.floating.move_dir_monitor("up"),

    # Tiled window movement
    (MOD, 'shift', 'h')     : pylewm.tiles.move_dir("left"),
    (MOD, 'shift', 'l')     : pylewm.tiles.move_dir("right"),
    (MOD, 'shift', 't')     : pylewm.tiles.move_dir("down"),
    (MOD, 'shift', 'n')     : pylewm.tiles.move_dir("up"),

    # Virtual desktop management
    (MOD, 'w')              : pylewm.desktops.next_desktop,
    (MOD, 'v')              : pylewm.desktops.prev_desktop,
    (MOD, 'z')              : pylewm.desktops.new_desktop,
    (MOD, 'shift', 'z')     : pylewm.desktops.window_new_desktop,

    # Move virtual desktops between monitors
    (MOD, 'lctrl', 'h')     : pylewm.desktops.move_dir_monitor("left"),
    (MOD, 'lctrl', 'l')     : pylewm.desktops.move_dir_monitor("right"),
    (MOD, 'lctrl', 't')     : pylewm.desktops.move_dir_monitor("down"),
    (MOD, 'lctrl', 'n')     : pylewm.desktops.move_dir_monitor("up"),

    # Yanking windows to scratch
    ## Windows yanked to scratch are hidden and can be dropped somewhere else
    (MOD, 'y')              : pylewm.scratch.yank,
    (MOD, 'i')              : pylewm.scratch.drop,
    (MOD, 'shift', 'i')     : pylewm.scratch.drop_all,

    # Layout control
    (MOD, 'd')              : pylewm.tiles.vsplit,
    (MOD, 'b')              : pylewm.tiles.hsplit,
    (MOD, 'shift', 'd')     : pylewm.tiles.vextend,
    (MOD, 'shift', 'b')     : pylewm.tiles.hextend,
    (MOD, 'e')              : pylewm.tiles.extend,
    (MOD, 'shift', 'e')     : pylewm.tiles.cancel_pending,

    # Window marks
    (MOD, 'm')              : pylewm.marks.mark_window,
    (MOD, "'")              : pylewm.marks.goto_window,

    # Default "control group" window marks
    (MOD, '&')              : pylewm.marks.goto_window("&"),
    (MOD, '[')              : pylewm.marks.goto_window("["),
    (MOD, '{')              : pylewm.marks.goto_window("{"),
    (MOD, '}')              : pylewm.marks.goto_window("}"),
    (MOD, '(')              : pylewm.marks.goto_window("("),
    (MOD, 'shift', '&')     : pylewm.marks.mark_window("&"),
    (MOD, 'shift', '[')     : pylewm.marks.mark_window("["),
    (MOD, 'shift', '{')     : pylewm.marks.mark_window("{"),
    (MOD, 'shift', '}')     : pylewm.marks.mark_window("}"),
    (MOD, 'shift', '(')     : pylewm.marks.mark_window("("),

    # Window management
    (MOD, '$')              : pylewm.windows.close,

    # Windows that are 'forgotten' are completely ignored by PyleWM until discovered again
    (MOD, 'alt', '#')       : pylewm.tiles.forget_window,
    (MOD, 'shift', '#')     : pylewm.tiles.discover_window,

    # Debug printing to console
    (MOD, '/')                 : pylewm.tiles.print_tree,
    (MOD, 'shift', '/')        : pylewm.floating.print_list,
    (MOD, 'alt', '/')          : pylewm.tiles.print_window_tree,
    (MOD, 'alt', 'shift', '/') : pylewm.tiles.print_rejected_windows,

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

# Any windows opened on a fullscreen tile automatically become new virtual desktops
pylewm.config["AutomaticDesktops"] = True

# Filters that determine properties of newly spawned windows
pylewm.config["Filters"] = [
    ({"title": "*qutebrowser*", "class": "QT5QWindowIcon"}, Tiling, NoTitlebar),
    ({"class": "mintty"}, NoTitlebar),
    ({"title": "Windows Shell Experience Host"}, Ignore),
    ({"title": "Store"}, Ignore),
    ({"title": "*Unreal Editor*", "child": False}, Tiling, Monitor(0), NewDesktop),
]

if __name__ == "__main__":
    for key, val in HOTKEYS.items():
        pylewm.hotkeys.register(key, val)
    pylewm.start()
