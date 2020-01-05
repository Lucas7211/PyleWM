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
    (MOD, 'x')    : pylewm.windows.drop_window_into_layout,

    # Space management

    # Tiling management

    # Application management
    (MOD, ',')              : pylewm.execution.start_menu,

    # PyleWM management
    (MOD, 'shift', 'q')     : pylewm.restart,
}

if __name__ == "__main__":
    for key, val in HOTKEYS.items():
        pylewm.hotkeys.register(key, val)
    pylewm.start()
