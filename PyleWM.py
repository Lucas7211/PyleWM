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
    (MOD, 'w')              : pylewm.tiles.focus_next,
    (MOD, 'v')              : pylewm.tiles.focus_prev,
    (MOD, 'h')              : pylewm.tiles.focus_dir("left"),
    (MOD, 'l')              : pylewm.tiles.focus_dir("right"),
    (MOD, 't')              : pylewm.tiles.focus_dir("down"),
    (MOD, 'n')              : pylewm.tiles.focus_dir("up"),
    
    # Layout control
    (MOD, 'd')              : pylewm.tiles.vsplit,
    (MOD, 'b')              : pylewm.tiles.hsplit,
    (MOD, 'shift', 'd')     : pylewm.tiles.vextend,
    (MOD, 'shift', 'b')     : pylewm.tiles.hetxend,
    (MOD, 'e')              : pylewm.tiles.extend, 
    (MOD, 'm')              : pylewm.tiles.cancel_pending,

    # Window management
    (MOD, '$')              : pylewm.windows.close,
    (MOD, '/')              : pylewm.tiles.print_tree,
    
    # Application management
    (MOD, ';')              : pylewm.execution.run(r"C:\cygwin64\bin\mintty.exe -"),
    (MOD, ',')              : pylewm.execution.start_menu,
    (MOD, 'shift', 'q')     : pylewm.quit,
}

if __name__ == "__main__":
    for key, val in HOTKEYS.items():
        pylewm.hotkeys.register(key, val)
    pylewm.start()