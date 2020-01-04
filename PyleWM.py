import pylewm

# Main modifier key that all the hotkeys are behind
MOD =                       'rctrl'

HOTKEYS = {
    # Window management
    (MOD, '$')    : pylewm.windows.close,

    # Space management

    # Tiling management

    # Application management
    #(MOD, '\\')    : pylewm.execution.start_menu,
    (MOD, 'shift', 'q')     : pylewm.restart,
}

if __name__ == "__main__":
    for key, val in HOTKEYS.items():
        pylewm.hotkeys.register(key, val)
    pylewm.start()
