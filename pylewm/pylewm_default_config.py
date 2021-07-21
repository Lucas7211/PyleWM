import pylewm
#import pylewm.modes.goto_window
#import pylewm.modes.select_application
#from pylewm.filters import *

import os

# Default hotkeys here are roughly based on i3wm equivalents
# (https://i3wm.org/docs/4.0/userguide.html#_default_keybindings)

def apply(MOD=('ctrl','alt')):
    pylewm.config.hotkeys({
        # -- MOD+HJKL moves the focus to a different window in that direction
        (*MOD, 'h')              : pylewm.spaces.focus_left,
        (*MOD, 'j')              : pylewm.spaces.focus_next,
        (*MOD, 'k')              : pylewm.spaces.focus_previous,
        (*MOD, 'l')              : pylewm.spaces.focus_right,

        ## -- MOD+SHIFT+HJKL moves the window into a tiling slot in that direction
        (*MOD, 'shift', 'h')     : pylewm.spaces.move_left,
        (*MOD, 'shift', 'j')     : pylewm.spaces.move_next,
        (*MOD, 'shift', 'k')     : pylewm.spaces.move_previous,
        (*MOD, 'shift', 'l')     : pylewm.spaces.move_right,

        ## -- MOD+Q closes the active window
        #(*MOD, 'q')              : pylewm.windows.close,

        ## -- MOD+M Minimizes a window
        #(*MOD, 'm')     : pylewm.windows.minimize,

        ## -- MOD+SHIFT+Z and X switch a window between being tiled and floating on top
        #(*MOD, 'shift', 'z')              : pylewm.windows.drop_window_into_layout,
        #(*MOD, 'shift', 'x')              : pylewm.windows.make_window_floating,

        ## -- Yank & Paste windows with MOD+Y and MOD+P
        #(*MOD, 'y')              : pylewm.yank.yank_window,
        #(*MOD, 'p')              : pylewm.yank.drop_window,
        #(*MOD, 'shift', 'p')     : pylewm.yank.drop_all_windows,

        ## -- MOD+Space to flip between the front and back sides of a monitor's desktop
        (*MOD, ' ')              : pylewm.spaces.flip,
        (*MOD, 'shift', ' ')     : pylewm.spaces.move_flip,

        ## -- MOD+Enter opens a fuzzy search window to start any application with a start menu / desktop shortcut
        #(*MOD, 'enter')          : pylewm.modes.select_application.run_application,

        ## -- MOD+W opens a fuzzy search window to select any available window by name
        #(*MOD, 'w')              : pylewm.modes.goto_window.start_goto_window,

        ## -- Temporary spaces are created and deleted when necessary per monitor
        (*MOD, 's')              : pylewm.spaces.goto_temporary,
        (*MOD, 'n')              : pylewm.spaces.next_temporary,
        (*MOD, 'm')              : pylewm.spaces.previous_temporary,

        (*MOD, 'shift', 's')     : pylewm.spaces.move_to_new_temporary_space,

        ## -- Application management
        (*MOD, 'a')              : pylewm.execution.command_prompt,
        (*MOD, 'd')              : pylewm.execution.start_menu,
        (*MOD, 'f')              : pylewm.execution.file_explorer,
        (*MOD, 'shift', 'f')     : pylewm.execution.this_pc,

        ## -- Reload PyleWM with MOD+SHIFT+R
        (*MOD, 'r')     : pylewm.run.restart,
        (*MOD, 'q')     : pylewm.run.quit,
    })