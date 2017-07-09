import pylewm
import pylewm.hotkeys
import pylewm.execution
import pylewm.windows

# Main modifier key that all the hotkeys are behind
MOD =                       'rctrl'

HOTKEYS = {    
    # Window management commands
    (MOD, 'h')              : pylewm.windows.focus_dir("left"),
    (MOD, 'l')              : pylewm.windows.focus_dir("right"),
    (MOD, 't')              : pylewm.windows.focus_dir("down"),
    (MOD, 'n')              : pylewm.windows.focus_dir("up"),
    (MOD, '$')              : pylewm.windows.close,
    
    # # Application management commands
    (MOD, ',')              : pylewm.execution.start_menu,
    (MOD, 'shift', 'q')     : pylewm.quit,
}

if __name__ == "__main__":
    for key, val in HOTKEYS.items():
        pylewm.hotkeys.register(key, val)
    pylewm.start()