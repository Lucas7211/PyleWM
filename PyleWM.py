import pylewm

# Main modifier key that all the hotkeys are behind
MOD =                       'rctrl'

HOTKEYS = {
    # Focus managament
    (MOD, 'h')    : pylewm.spaces.focus_left,
    (MOD, 's')    : pylewm.spaces.focus_right,
    (MOD, 't')    : pylewm.spaces.focus_next,
    (MOD, 'n')    : pylewm.spaces.focus_previous,

    # Move window slots
    (MOD, 'shift', 'h')    : pylewm.spaces.move_left,
    (MOD, 'shift', 's')    : pylewm.spaces.move_right,
    (MOD, 'shift', 't')    : pylewm.spaces.move_next,
    (MOD, 'shift', 'n')    : pylewm.spaces.move_previous,

    # Window management
    (MOD, '$')    : pylewm.windows.close,
    (MOD, ']')    : pylewm.windows.poke,
    (MOD, 'x')    : pylewm.windows.drop_window_into_layout,

    # Space management
    (MOD, 'j')    : pylewm.spaces.flip,
    (MOD, ' ')    : pylewm.spaces.flip,

    (MOD, 'z')    : pylewm.spaces.goto_temporary,
    (MOD, 'w')    : pylewm.spaces.next_temporary,
    (MOD, 'v')    : pylewm.spaces.previous_temporary,

    (MOD, 'shift', 'z')    : pylewm.spaces.move_to_new_temporary_space,

    # Tiling management

    # Application management
    (MOD, ',')              : pylewm.execution.start_menu,

    # PyleWM management
    (MOD, 'shift', 'q')     : pylewm.restart,
    (MOD, '\\')             : pylewm.spaces.print_state,
}

if __name__ == "__main__":
    for key, val in HOTKEYS.items():
        pylewm.hotkeys.register(key, val)
    pylewm.start()
