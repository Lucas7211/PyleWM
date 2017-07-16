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
            if not self.containsWindow(self.focusedWindow):
                self.focusedWindow = None

        self.monitor = monitor

    def containsWindow(self, window):
        for win in self.floating:
            if win.isChildOf(window) or win.isParentOf(window):
                return True
        return self.tileContains(self.tile, window)

    def tileContains(self, tile, window):
        if hasattr(tile, "window") and tile.window == window:
            return True
        for child in tile.childList:
            if self.tileContains(child, window):
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
