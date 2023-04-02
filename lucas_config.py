# This is my own config. I put this in the git repo because I am very important.
# Keys are based on a custom dvorak keyboard layout.

import pylewm
import pylewm.modes
import pylewm.modes.hint_mouse
import pylewm.modes.hint_window
import pylewm.modes.hint_mouse
import pylewm.modes.keynav
import pylewm.modes.goto_window
import pylewm.modes.select_application
import pylewm.modes.execute_task
import pylewm.modes.window_switcher
import pylewm.modes.retrieve_hidden_window
from pylewm.filters import *

pylewm.config.AllowDroppingIntoLayout = False
pylewm.config.HideTaskbar = True

# I have remapped the 'app' key to a more convenient place on the keyboard
# and use it for all my window management shortcuts.
MOD = ('app',)

def GoToSleep():
    pylewm.hotkeys.clear()
    pylewm.execution.run([r'C:\bin\GoToSleep.bat'], cmd_window=True).run()

pylewm.config.hotkeys({
    # Focus management
    (*MOD, 'h')              : pylewm.spaces.focus_left,
    (*MOD, 's')              : pylewm.spaces.focus_right,
    (*MOD, '/')              : pylewm.spaces.focus_right,
    (*MOD, 't')              : pylewm.spaces.focus_down,
    (*MOD, 'n')              : pylewm.spaces.focus_up,

    (*MOD, '&')              : pylewm.focus.focus_monitor(-1),
    (*MOD, '[')              : pylewm.focus.focus_monitor(0),
    (*MOD, '{')              : pylewm.focus.focus_monitor(1),
    (*MOD, '}')              : pylewm.focus.focus_monitor(2),

    # Move window slots
    (*MOD, 'shift', 'h')     : pylewm.spaces.move_left,
    (*MOD, 'shift', 's')     : pylewm.spaces.move_right,
    (*MOD, 'shift', '/')     : pylewm.spaces.move_right,
    (*MOD, 'shift', 't')     : pylewm.spaces.move_down,
    (*MOD, 'shift', 'n')     : pylewm.spaces.move_up,

    (*MOD, 'shift', 'lctrl', 'h')     : pylewm.spaces.move_insert_left,
    (*MOD, 'shift', 'lctrl', 's')     : pylewm.spaces.move_insert_right,
    (*MOD, 'shift', 'lctrl', 't')     : pylewm.spaces.move_down,
    (*MOD, 'shift', 'lctrl', 'n')     : pylewm.spaces.move_up,

    (*MOD, 'shift', '&')     : pylewm.windows.move_to_monitor(-1),
    (*MOD, 'shift', '[')     : pylewm.windows.move_to_monitor(0),
    (*MOD, 'shift', '{')     : pylewm.windows.move_to_monitor(1),
    (*MOD, 'shift', '}')     : pylewm.windows.move_to_monitor(2),

    # Window management
    (*MOD, '$')              : pylewm.windows.close,
    (*MOD, '@')              : pylewm.windows.close,
    (*MOD, '\\')             : pylewm.windows.poke,
    (*MOD, "'")              : pylewm.windows.drop_window_into_layout,

    (*MOD, 'shift', 'm')     : pylewm.windows.minimize,

    (*MOD, 'y')              : pylewm.yank.yank_window,
    (*MOD, 'shift', 'y')     : pylewm.yank.yank_window(detach_from_tab_group=True),
    (*MOD, 'i')              : pylewm.yank.drop_window,
    (*MOD, 'shift', 'i')     : pylewm.yank.drop_window_into_tab_group,

    (*MOD, 'x')              : pylewm.zoom.toggle_zoomed,

    # Space management
    (*MOD, ' ')              : pylewm.spaces.flip,
    (*MOD, 'shift', ' ')     : pylewm.spaces.move_flip,

    (*MOD, 'o')              : pylewm.spaces.goto_temporary,
    (*MOD, 'w')              : pylewm.spaces.next_temporary,
    (*MOD, 'v')              : pylewm.spaces.previous_temporary,

    (*MOD, 'shift', 'o')     : pylewm.spaces.move_to_new_temporary_space,

    (*MOD, 'g')              : pylewm.spaces.focus_space(-1, 0),
    (*MOD, 'c')              : pylewm.spaces.focus_space(0, 0),
    (*MOD, 'r')              : pylewm.spaces.focus_space(1, 0),
    (*MOD, 'l')              : pylewm.spaces.focus_space(2, 0),

    (*MOD, '*')              : pylewm.spaces.focus_space(-1, 1),
    (*MOD, ')')              : pylewm.spaces.focus_space(0, 1),
    (*MOD, '+')              : pylewm.spaces.focus_space(1, 1),
    (*MOD, ']')              : pylewm.spaces.focus_space(2, 1),

    (*MOD, 'shift', 'g')     : pylewm.spaces.move_to_space(-1, 0),
    (*MOD, 'shift', 'c')     : pylewm.spaces.move_to_space(0, 0),
    (*MOD, 'shift', 'r')     : pylewm.spaces.move_to_space(1, 0),
    (*MOD, 'shift', 'l')     : pylewm.spaces.move_to_space(2, 0),

    (*MOD, 'shift', '*')     : pylewm.spaces.move_to_space(-1, 1),
    (*MOD, 'shift', ')')     : pylewm.spaces.move_to_space(0, 1),
    (*MOD, 'shift', '+')     : pylewm.spaces.move_to_space(1, 1),
    (*MOD, 'shift', ']')     : pylewm.spaces.move_to_space(2, 1),

    (*MOD, 'a')              : pylewm.dropdown.toggle_dropdown,
    (*MOD, 'shift', 'a')     : pylewm.dropdown.set_as_dropdown,

    # Tab management
    (*MOD, 'm')              : pylewm.tabs.make_next_window_tabbed,
    (*MOD, 'z')              : pylewm.tabs.next_tab,
    (*MOD, 'shift', 'z')     : pylewm.tabs.move_tab_next,
    (*MOD, 'b')              : pylewm.tabs.previous_tab,
    (*MOD, 'shift', 'b')     : pylewm.tabs.move_tab_previous,
    (*MOD, 'ctrl', 't')      : pylewm.tabs.duplicate_window_into_tab,
    (*MOD, "shift", "'")     : pylewm.tabs.detach_window_from_tab_group,

    # Application management
    (*MOD, ';')              : pylewm.execution.run([r'C:\Program Files\Alacritty\alacritty.exe']),
    (*MOD, 'shift', ';')     : pylewm.execution.run([r'C:\Program Files\Alacritty\alacritty.exe', '-e', 'powershell'], as_admin=True),
    (*MOD, 'ctrl', ',')      : pylewm.execution.toggle_taskbar_visibility,
    (*MOD, 'p')              : pylewm.execution.run(r'C:\Program Files\Mozilla Firefox\firefox.exe'),
    (*MOD, 'k')              : pylewm.execution.run([r'C:\Program Files\Alacritty\alacritty.exe', '-e', 'wsl.exe', "--", "ranger", "/data/spool"]),
    (*MOD, 'u')              : pylewm.execution.this_pc,
    (*MOD, 'shift', 'u')     : pylewm.execution.file_explorer,

    (*MOD, '.')              : pylewm.execution.run([r'C:\mpd\toggle.bat']),
    (*MOD, 'shift', '.')     : pylewm.execution.run([r'C:\mpd\mpc.exe', 'next']),

    (*MOD, 'tab')            : pylewm.execution.start_screenclip,
    (*MOD, 'shift', 'p')     : pylewm.modes.execute_task.start_execute_task,
        
    # PyleWM management
    (*MOD, 'shift', 'q')     : pylewm.run.restart,
    ('any_mod', '=app')      : pylewm.window_drag.activate_window_drag_resize,

    # List selection modes
    (*MOD, ',')              : pylewm.modes.select_application.run_application,
    (*MOD, 'enter')          : pylewm.modes.goto_window.start_goto_window,
    (*MOD, 'shift', 'enter') : pylewm.modes.hint_mouse.start_hint_mouse(hintkeys="aoeuhtns"),
    (*MOD, 'e')              : pylewm.modes.window_switcher.start_window_switcher(hintkeys="aoeuhtns"),
    (*MOD, 'f')              : pylewm.modes.hint_window.start_hint_window(hintkeys="aoeuhtns"),
    (*MOD, 'shift', 'f')     : pylewm.modes.hint_window.start_hint_floating_window(hintkeys="aoeuhtns"),

    # Copy-paste shortcuts
    (*MOD, 'q')              : pylewm.sendkeys.sendkey(('ctrl', 'c')),
    (*MOD, 'j')              : pylewm.sendkeys.sendkey(('ctrl', 'v')),
    (*MOD, 'u')              : pylewm.sendkeys.sendkey(('ctrl', 'z')),
    (*MOD, 'shift', 'u')     : pylewm.sendkeys.sendkey(('ctrl', 'y')),

    # Unicode shortcuts
    (*MOD, '-')              : pylewm.hotkeys.Mode(
        oneshot=True,
        hotkeys={
            "-" : pylewm.sendkeys.sendtext("—"),
            "." : pylewm.sendkeys.sendtext("…"),
            "a" : pylewm.sendkeys.sendtext("å"),
            "e" : pylewm.sendkeys.sendtext("ä"),
            "o" : pylewm.sendkeys.sendtext("ö"),
            ('shift', 'a') : pylewm.sendkeys.sendtext("Å"),
            ('shift', 'e') : pylewm.sendkeys.sendtext("Ä"),
            ('shift', 'o') : pylewm.sendkeys.sendtext("Ö"),
            "h" : pylewm.sendkeys.sendtext("←"),
            "t" : pylewm.sendkeys.sendtext("↓"),
            "n" : pylewm.sendkeys.sendtext("↑"),
            "s" : pylewm.sendkeys.sendtext("→"),
        },
    ),

    # System management
    (*MOD, 'ctrl', '$')     : GoToSleep,
})

pylewm.config.filters([
    ({"class": "mintty"}, NoTitlebar, AutoPoke),
    ({"title": "Windows Terminal"}, NoTitlebar),
    ({"title": "Slack *"}, Tiling, Monitor(2)),
    ({"title": "* Discord"}, Tiling, Monitor(2)),
    ({"class": "MediaPlayerClassicW"}, Floating),

    # Visual Studio
    ({"class": "HwndWrapper[*"}, KeepStartMonitor, AutoPoke, ForceBorders(2)),
    ({"class": "Ghost"}, Ignore),

    # Unreal Engine
    ({"title": "*Unreal Editor*", "child": False}, Tiling, Monitor(1), TemporarySpace),
    ({"class": "SplashScreenClass"}, Ignore),
    ({"class": "UnrealWindow", "child": True}, Floating),
    ({"title": "*PCD3D_SM5*", "class": "UnrealWindow"}, Tiling, Monitor(1), TemporarySpace),
])
