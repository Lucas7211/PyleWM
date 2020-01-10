import pylewm
import os
from pylewm.filters import *

# Main modifier key that all the hotkeys are behind
MOD =                       'rctrl'

HOTKEYS = {
    # Focus managament
    (MOD, 'h')              : pylewm.spaces.focus_left,
    (MOD, 's')              : pylewm.spaces.focus_right,
    (MOD, 't')              : pylewm.spaces.focus_next,
    (MOD, 'n')              : pylewm.spaces.focus_previous,

    (MOD, '&')              : pylewm.focus.focus_monitor(0),
    (MOD, '[')              : pylewm.focus.focus_monitor(1),
    (MOD, '{')              : pylewm.focus.focus_monitor(2),
    (MOD, '}')              : pylewm.focus.focus_monitor(3),

    # Move window slots
    (MOD, 'shift', 'h')     : pylewm.spaces.move_left,
    (MOD, 'shift', 's')     : pylewm.spaces.move_right,
    (MOD, 'shift', 't')     : pylewm.spaces.move_next,
    (MOD, 'shift', 'n')     : pylewm.spaces.move_previous,

    (MOD, 'shift', '&')     : pylewm.windows.move_to_monitor(0),
    (MOD, 'shift', '[')     : pylewm.windows.move_to_monitor(1),
    (MOD, 'shift', '{')     : pylewm.windows.move_to_monitor(2),
    (MOD, 'shift', '}')     : pylewm.windows.move_to_monitor(3),

    # Window management
    (MOD, '$')              : pylewm.windows.close,
    (MOD, '\\')             : pylewm.windows.poke,
    (MOD, "'")              : pylewm.windows.drop_window_into_layout,
    (MOD, 'x')              : pylewm.windows.make_window_floating,

    (MOD, 'shift', 'm')     : pylewm.windows.minimize,
    (MOD, 'shift', 'b')     : pylewm.windows.vanish,

    (MOD, 'y')              : pylewm.yank.yank_window,
    (MOD, 'i')              : pylewm.yank.drop_window,
    (MOD, 'shift', 'i')     : pylewm.yank.drop_all_windows,

    # Space management
    (MOD, 'j')              : pylewm.spaces.flip,
    (MOD, 'shift', 'j')     : pylewm.spaces.move_flip,
    (MOD, ' ')              : pylewm.spaces.flip,
    (MOD, 'shift', ' ')     : pylewm.spaces.move_flip,

    (MOD, 'o')              : pylewm.spaces.goto_temporary,
    (MOD, 'w')              : pylewm.spaces.next_temporary,
    (MOD, 'v')              : pylewm.spaces.previous_temporary,

    (MOD, 'shift', 'o')     : pylewm.spaces.move_to_new_temporary_space,

    (MOD, 'g')              : pylewm.spaces.focus_space(0, 0),
    (MOD, 'c')              : pylewm.spaces.focus_space(1, 0),
    (MOD, 'r')              : pylewm.spaces.focus_space(2, 0),
    (MOD, 'l')              : pylewm.spaces.focus_space(3, 0),

    (MOD, '*')              : pylewm.spaces.focus_space(0, 1),
    (MOD, ')')              : pylewm.spaces.focus_space(1, 1),
    (MOD, '+')              : pylewm.spaces.focus_space(2, 1),
    (MOD, ']')              : pylewm.spaces.focus_space(3, 1),

    (MOD, 'shift', 'g')     : pylewm.spaces.move_to_space(0, 0),
    (MOD, 'shift', 'c')     : pylewm.spaces.move_to_space(1, 0),
    (MOD, 'shift', 'r')     : pylewm.spaces.move_to_space(2, 0),
    (MOD, 'shift', 'l')     : pylewm.spaces.move_to_space(3, 0),

    (MOD, 'shift', '*')     : pylewm.spaces.move_to_space(0, 1),
    (MOD, 'shift', ')')     : pylewm.spaces.move_to_space(1, 1),
    (MOD, 'shift', '+')     : pylewm.spaces.move_to_space(2, 1),
    (MOD, 'shift', ']')     : pylewm.spaces.move_to_space(3, 1),

    (MOD, '!')              : pylewm.spaces.next_layout,
    (MOD, 'shift', '!')     : pylewm.spaces.previous_layout,

    # Application management
    (MOD, ';')              : pylewm.wsltty.open_wsltty,
    (MOD, 'a')              : pylewm.execution.run(['cmd.exe']),
    (MOD, 'shift', 'a')     : pylewm.execution.run(['start', 'cmd.exe'], drop_admin=False),
    (MOD, ',')              : pylewm.execution.start_menu,
    (MOD, 'p')              : pylewm.execution.run(r'C:\Program Files\Mozilla Firefox\firefox.exe'),
    (MOD, 'k')              : pylewm.wsltty.open_wsltty(["ranger", pylewm.wsltty.wsl_path(os.environ["USERPROFILE"])]),
    (MOD, 'u')              : pylewm.execution.run(r'explorer.exe'),

    # PyleWM management
    (MOD, 'shift', 'q')     : pylewm.restart,
    (MOD, 'shift', '\\')    : pylewm.windows.show_window_info,
    (MOD, 'shift', '=')     : pylewm.spaces.show_spaces_info,
}

pylewm.filters.Filters = [
    ({"class": "mintty"}, NoTitlebar, AutoPoke),
    ({"title": "Slack *"}, Tiling, Monitor(0)),
    ({"title": "*Media Player Classic*"}, Floating),
    ({"title": "* One Manager"}, Tiling, Monitor(2), TemporarySpace),

    # Visual Studio
    ({"class": "HwndWrapper[*"}, KeepStartMonitor, AutoPoke),
    ({"class": "Ghost"}, Ignore),

    # Unreal Engine
    ({"title": "*Unreal Editor*", "child": False}, Tiling, Monitor(1), TemporarySpace),
    ({"class": "SplashScreenClass"}, Ignore),
    ({"class": "UnrealWindow", "child": True}, Floating),
    ({"title": "*PCD3D_SM5*", "class": "UnrealWindow"}, Tiling, Monitor(1), TemporarySpace),
]

if __name__ == "__main__":
    for key, val in HOTKEYS.items():
        pylewm.hotkeys.register(key, val)
    pylewm.start()
