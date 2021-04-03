PyleWM
======
PyleWM is a utility for doing tiled window management on the Windows OS.
It is inspired heavily by the linux window managers i3 and awesomewm.

Functionality includes:
* Windows are automatically tiled into a column-grid layout. Hotkeys can be used
  to move or swap windows in the grid.
* Hotkeys for switching which window is focused based on a direction.
* Double-sided workspaces per monitor, allowing for easy flipping back and forth.
* Binding arbitrary global hotkeys to various builtins or any python function.
* Any number of temporary workspaces per monitor, created as needed.
* Drag & Drop windows into automatically tiled slots.

Installation
============
Either:
* Download a self-contained binary package from the [Releases Page](https://github.com/GGLucas/PyleWM/releases)
* OR: Use `pip install pylewm` and run `python -m pylewm`
* OR: Clone the repository and execute `PyleWM.py` (see Dependencies section below)

Getting Started
===============
When you start PyleWM you will find all your windows tiled into a grid
automatically.

Holding `Control+Alt` and pressing one of the `HJKL` keys will automatically
change your focused window in the direction of the pressed key.
Holding `Control+Alt+Shift` and pressing one of the `HJKL` keys will move
the window in that direction in the grid.

Grabbing a window with the mouse and moving it around pops it out of
the tiled grid automatically. You can then drop it back into the
grid by dropping it with the mouse hovered near one of the vertical
splits in the grid layout. An empty space will be shown indicating
where the window will be dropped.

Pressing `Control+Alt+Space` will swap the monitor's workspace between
the 'back' and 'front', allowing you to have two separate tiling layouts.

For a list of hotkeys available by default see [the example config file](pylewm/pylewm_example_config.py).

PyleWM adds a windows tray icon that can be used to quit the application.

Temporary Workspaces
====================
In addition to the two 'back' and 'front' workspaces per monitor, an unlimited
amount of temporary workspaces can be used.

Temporary workspaces only exist as long as there are windows assigned to them.
As soon as all windows in a temporary workspace are closed or moved away, it is destroyed.

The default `Control+Alt+S` shortcut will switch to the most recently used temporary workspace. 
When there are no temporary workspaces on this monitor, or if the current visible workspace is already a temporary workspace,
it switches to a new empty temporary workspace instead.

The `Control+Alt+N` (Next Temporary Workspace) and `Control+Alt+M` (Previous Temporary Workspace) shortcuts can
switch between temporary workspaces if the current monitor has more than one.

Pressing `Control+Alt+Shift+S` will move the currently focused window into its own new temporary workspace.

Configuration
=============
PyleWM automatically sets up an example configuration file in
`%APPDATA%\PyleWM\PyleWM_Config.py`. Change the configuration and 
restart PyleWM (default hotkey `Control+Alt+Shift+R`) to load the
updated configuration.

Dependencies
============
Written for minimum Python version 3.6.
Requires `pypiwin32`, `pystray`, `pygame`, `fuzzywuzzy`, and `pylnk3`.

Permissions
===========
Unfortunately, PyleWM will have to run as administrator (it prompts UAC
when ran as user). Windows does not allow window management on system
windows such as Task Manager unless administrator permissions are active, and 
PyleWM would stop working.

Focus Stealing
==============
Since PyleWM has a lot of features to set the focused window using keyboard control,
we have to work around Windows' limitations that prevent focus from changing in 
certain situations. One such limitation is a timeout in the rate that focus can be switched.

To make switching focus using PyleWM more consistent, running PyleWM automatically sets the
`HKCU\Control Panel\Desktop\ForegroundLockTimeout` registry value to 0 to allow
windows to be unfocused.

You may need to sign out of your user account and sign back in before this takes effect.