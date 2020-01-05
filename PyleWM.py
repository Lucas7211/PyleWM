import pylewm
import os
from pylewm.filters import NoTitlebar, Tiling, Floating, Monitor, TemporarySpace, Ignore, AutoPoke

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
    (MOD, '!')              : pylewm.windows.poke,
    (MOD, 'x')              : pylewm.windows.drop_window_into_layout,
    (MOD, 'shift', 'm')     : pylewm.windows.minimize,

    (MOD, 'y')              : pylewm.yank.yank_window,
    (MOD, 'i')              : pylewm.yank.drop_window,
    (MOD, 'shift', 'i')     : pylewm.yank.drop_all_windows,

    # Space management
    (MOD, 'j')              : pylewm.spaces.flip,
    (MOD, 'shift', 'j')     : pylewm.spaces.move_flip,
    (MOD, ' ')              : pylewm.spaces.flip,
    (MOD, 'shift', ' ')     : pylewm.spaces.move_flip,

    (MOD, 'z')              : pylewm.spaces.goto_temporary,
    (MOD, 'w')              : pylewm.spaces.next_temporary,
    (MOD, 'v')              : pylewm.spaces.previous_temporary,

    (MOD, 'shift', 'z')     : pylewm.spaces.move_to_new_temporary_space,

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

    # Tiling management

    # Application management
    (MOD, ';')              : pylewm.wsltty.open_wsltty,
    (MOD, 'shift', ';')     : pylewm.execution.run(['start', 'cmd.exe']),
    (MOD, ',')              : pylewm.execution.start_menu,
    (MOD, 'p')              : pylewm.execution.run(r'C:\Program Files\Mozilla Firefox\firefox.exe'),
    (MOD, 'k')              : pylewm.wsltty.open_wsltty(["ranger", pylewm.wsltty.wsl_path(os.environ["USERPROFILE"])]),
    (MOD, 'shift', 'k')     : pylewm.execution.run(r'explorer.exe'),

    # PyleWM management
    (MOD, 'shift', 'q')     : pylewm.restart,
    (MOD, '\\')             : pylewm.spaces.print_state,
}

pylewm.filters.Filters = [
    ({"class": "mintty"}, NoTitlebar, AutoPoke),
    ({"class": "OperationStatusWindow"}, Floating),
    ({"class": "TaskManagerWindow"}, Ignore),
    ({"title": "*Unreal Editor*", "child": False}, Tiling, Monitor(0), TemporarySpace),
]

if __name__ == "__main__":
    for key, val in HOTKEYS.items():
        pylewm.hotkeys.register(key, val)
    pylewm.start()
