import pylewm
import pylewm.hotkeys
import pylewm.execution
import pylewm.windows
import pylewm.monitors
import pylewm.tiles

# Main modifier key that all the hotkeys are behind
MOD =                       'rctrl'

HOTKEYS = {    
    # Window focus control
    (MOD, 'h')              : pylewm.tiles.focus_dir("left"),
    (MOD, 'l')              : pylewm.tiles.focus_dir("right"),
    (MOD, 't')              : pylewm.tiles.focus_dir("down"),
    (MOD, 'n')              : pylewm.tiles.focus_dir("up"),
    (MOD, 'w')              : pylewm.tiles.switch_next,
    (MOD, 'v')              : pylewm.tiles.switch_prev,
    
    # Window movement
    (MOD, 'shift', 'h')     : pylewm.tiles.move_dir("left"),
    (MOD, 'shift', 'l')     : pylewm.tiles.move_dir("right"),
    (MOD, 'shift', 't')     : pylewm.tiles.move_dir("down"),
    (MOD, 'shift', 'n')     : pylewm.tiles.move_dir("up"),
    
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
    (MOD, ';')              : pylewm.execution.run(r'C:\cygwin64\bin\mintty.exe -'),
    (MOD, ',')              : pylewm.execution.start_menu,
    (MOD, 'p')              : pylewm.execution.run(r'"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"'),
    (MOD, 'k')              : pylewm.execution.run(r'explorer.exe'),
    (MOD, 'shift', 'q')     : pylewm.quit,
}

# Teleport the mouse to any window that focus has been switched to
pylewm.config["TeleportMouse"] = True

if __name__ == "__main__":
    for key, val in HOTKEYS.items():
        pylewm.hotkeys.register(key, val)
    pylewm.start()