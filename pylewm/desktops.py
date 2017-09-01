from pylewm import pyleinit, pylecommand
import win32gui, win32con, win32api

import pylewm.tiles
import pylewm.floating
import pylewm.rects
import pylewm.focus
import pylewm.monitors

@pylecommand
def next_desktop():
    """ Switch to the next virtual desktop on the focused monitor. """
    monitor = getFocusMonitor()
    if monitor is not None:
        if not monitor.desktops:
            return

        curDesktop = StoredDesktop(monitor)

        if not curDesktop.empty():
            monitor.desktops.append(curDesktop)
        newDesktop = monitor.desktops.pop(0)

        newDesktop.show()

@pylecommand
def prev_desktop():
    """ Switch to the previous virtual desktop on the focused monitor. """
    monitor = getFocusMonitor()
    if monitor is not None:
        if not monitor.desktops:
            return

        curDesktop = StoredDesktop(monitor)

        if not curDesktop.empty():
            monitor.desktops.insert(0, curDesktop)
        newDesktop = monitor.desktops.pop()

        newDesktop.show()

@pylecommand
def new_desktop():
    """ Create a new empty virtual desktop on the focused monitor. """
    monitor = getFocusMonitor()
    print(f"NEW DESKTOP {monitor}")
    if monitor is not None:
        curDesktop = StoredDesktop(monitor)
        if not curDesktop.empty():
            monitor.desktops.append(curDesktop)
        pylewm.tiles.newMonitorTile(monitor.rect)

@pylecommand
def move_dir_monitor(dir="left"):
    """ Move the focused virtual desktop to a different monitor in a direction. """
    monitor = getFocusMonitor()
    targetMonitor = pylewm.monitors.getMonitorInDirection(monitor.rect, dir)

    print(f"MOVE DESKTOP FROM {monitor.rect} (x{len(monitor.desktops)}) TO {targetMonitor.rect}")
    pylewm.tiles.print_tree()
    pylewm.floating.print_list()

    # Store the windows on the monitor we're replacing
    targetDesktop = StoredDesktop(targetMonitor)
    if not targetDesktop.empty():
        targetMonitor.desktops.append(targetDesktop)

    # Grab and move the windows on the source monitor
    curDesktop = StoredDesktop(monitor, banish=False)
    if not curDesktop.empty():
        curDesktop.monitor = targetMonitor
        curDesktop.moveIntoRelative(targetMonitor.rect)
        curDesktop.show(summon=False)
    else:
        pylewm.tiles.newMonitorTile(targetMonitor.rect)

    # Open or create a remaining desktop on the source monitor
    if monitor.desktops:
        remainingDesktop = monitor.desktops.pop(0)
        remainingDesktop.show()
    else:
        pylewm.tiles.newMonitorTile(monitor.rect)

    curDesktop.tile.focus()

    print(f"AFTERWARD:")
    pylewm.tiles.print_tree()
    pylewm.floating.print_list()
    pylewm.tiles.teleportMouse(curDesktop.tile)

@pylecommand
def window_new_desktop():
    """ Move the active window to a new desktop of its own. """
    curWindow = win32gui.GetForegroundWindow()
    if not win32gui.IsWindow(curWindow):
        return

    new_desktop_with_window(curWindow)

def new_desktop_with_window(curWindow):
    # Remove the window from the system
    isFloating = pylewm.floating.isFloatingWindow(curWindow)
    if isFloating:
        pylewm.floating.stopFloatingWindow(curWindow, keepFloatingFocus=False)
    else:
        pylewm.tiles.stopTilingWindow(curWindow, keepTilingFocus=False, reposition=False)

    # Create a new desktop on the window's monitor
    monitorIndex = pylewm.filters.get_monitor(curWindow)
    if monitorIndex == -1:
        monitor = pylewm.monitors.getMonitor(win32gui.GetWindowRect(curWindow))
        if monitor is None:
            monitorIndex = 0
        else:
            monitorIndex = pylewm.monitors.Monitors.index(monitor)
    else:
        monitor = pylewm.monitors.Monitors[monitorIndex]

    if monitor is not None:
        curDesktop = StoredDesktop(monitor)
        if not curDesktop.empty():
            monitor.desktops.append(curDesktop)
        pylewm.tiles.newMonitorTile(monitor.rect)

    # Re-add the window back
    if isFloating:
        pylewm.floating.startFloatingWindow(curWindow)
    else:
        pylewm.tiles.startTilingWindow(curWindow, secondary=True)

class StoredDesktop:
    def __init__(self, monitor, banish=True):
        print(f"STORE DESKTOP {monitor.rect}")
        self.focusedWindow = win32gui.GetForegroundWindow()
        self.focusedTile = None
        if not pylewm.floating.isFloatingFocused():
            self.focusedTile = pylewm.tiles.FocusTile

        self.tile = pylewm.tiles.takeMonitorTile(monitor.rect, banish=banish)
        self.floating = []
        for win in pylewm.floating.FloatingWindows[:]:
            # Don't grab child windows, the parent handles them for us
            if win32gui.IsWindow(win32api.GetWindowLong(win.window, win32con.GWL_HWNDPARENT)):
                continue

            # Check if this is our monitor
            if pylewm.monitors.getMonitor(win32gui.GetWindowRect(win.window)) is monitor:
                pylewm.floating.takeFloatingWindow(win)
                if banish:
                    win.banish()
                self.floating.append(win)

        if self.focusedTile is not None:
            if not self.focusedTile.isChildOf(self.tile):
                self.focusedTile = None
        if self.focusedWindow is not None:
            if not self.contains_window(self.focusedWindow):
                self.focusedWindow = None

        self.monitor = monitor

    def contains_window(self, window):
        for win in self.floating:
            if win.isChildOf(window) or win.isParentOf(window):
                return True
        return self.tile_contains(self.tile, window)

    def tile_contains(self, tile, window):
        if hasattr(tile, "window") and tile.window == window:
            return True
        for child in tile.childList:
            if self.tile_contains(child, window):
                return True
        return False

    def show(self, summon=True):
        print(f"SHOW DESKTOP {self.monitor.rect}")
        for win in self.floating:
            if summon:
                win.summon()
            pylewm.floating.returnFloatingWindow(win)
        pylewm.tiles.returnMonitorTile(self.tile, summon=summon)

        if self.focusedTile is not None:
            self.focusedTile.focus()
        elif win32gui.IsWindow(self.focusedWindow):
            print(f"SET FLOATING FOCUS {self.focusedWindow}")
            pylewm.focus.set(self.focusedWindow)
        else:
            self.tile.focus()

    def empty(self):
        if len(self.tile.childList) != 0:
            return False
        return True

    def moveIntoRelative(self, targetRect):
        sourceRect = self.tile.rect
        self.moveTilesRelative(self.tile, sourceRect, targetRect)

        for win in self.floating:
            pylewm.floating.moveWindow(win.window, pylewm.rects.moveRelativeInto(win.rect, sourceRect, targetRect))

    def moveTilesRelative(self, tile, sourceRect, targetRect):
        tile.rect = pylewm.rects.moveRelativeInto(tile.rect, sourceRect, targetRect)
        for child in tile.childList:
            self.moveTilesRelative(child, sourceRect, targetRect)

def getFocusMonitor():
    win = win32gui.GetForegroundWindow()
    monitor = None

    cursorPos = win32gui.GetCursorPos()
    mouseMonitor = pylewm.monitors.getMonitor(cursorPos)

    if win is None:
        return mouseMonitor
    elif len(pylewm.tiles.getCurrentMonitorTile(cursorPos).childList) == 0:
        return mouseMonitor
    else:
        return pylewm.monitors.getMonitor(win32gui.GetWindowRect(win))

def find_with_window(window):
    """ Find the desktop that contains this window. """
    for mon in pylewm.monitors.Monitors:
        for desktop in mon.desktops:
            if desktop.contains_window(window):
                return desktop
    return None

def switch_to_containing(window):
    """ Switch to the desktop that contains this window, if one exists. """
    desktop = find_with_window(window)
    if desktop is not None:
        monitor = desktop.monitor

        # Store the current desktop on that monitor
        newDesktop = StoredDesktop(monitor)
        if not newDesktop.empty():
            monitor.desktops.append(newDesktop)

        # Rotate through desktops until we get to the one we want to focus
        while monitor.desktops[0] is not desktop:
            monitor.desktops.append(monitor.desktops.pop(0))

        # Show the desktop we want to focus
        monitor.desktops.pop(0)
        desktop.show()
