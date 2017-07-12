from pylewm import pyleinit, pylecommand
import win32gui, win32con, win32api

import pylewm.tiles
import pylewm.floating
import pylewm.rects
import pylewm.focus

Monitors = []
DesktopArea = [0,0,0,0]

@pylecommand
def nextDesktop():
    monitor = getFocusMonitor()
    if monitor is not None:
        monitor.switchNextDesktop()

@pylecommand
def prevDesktop():
    monitor = getFocusMonitor()
    if monitor is not None:
        monitor.switchPrevDesktop()

@pylecommand
def newDesktop():
    monitor = getFocusMonitor()
    print(f"NEW DESKTOP {monitor}")
    if monitor is not None:
        monitor.newDesktop()

class StoredDesktop:
    def __init__(self, monitor):
        print(f"STORE DESKTOP {monitor.rect}")
        self.focusedWindow = win32gui.GetForegroundWindow()
        self.focusedTile = None
        if not pylewm.floating.isFloatingFocused():
            self.focusedTile = pylewm.tiles.FocusTile

        self.tile = pylewm.tiles.takeMonitorTile(monitor.rect)
        self.floating = []
        for win in pylewm.floating.FloatingWindows[:]:
            # Don't grab child windows, the parent handles them for us
            if win32gui.IsWindow(win.parent):
                continue

            # Check if this is our monitor
            if getMonitor(win32gui.GetWindowRect(win.window)) is monitor:
                pylewm.floating.takeFloatingWindow(win)
                win.banish()
                self.floating.append(win)

        if self.focusedTile is not None:
            if not self.focusedTile.isChildOf(self.tile):
                self.focusedTile = None

        self.monitor = monitor

    def show(self):
        print(f"SHOW DESKTOP {self.monitor.rect}")
        for win in self.floating:
            win.summon()
            pylewm.floating.returnFloatingWindow(win)
        pylewm.tiles.returnMonitorTile(self.tile)

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

class Monitor:
    def __init__(self, info):
        self.info = info
        self.rect = info['Monitor']
        self.desktops = []

    def getNextDesktop(self):
        if not self.desktops:
            return None
        return self.desktops[0]

    def getPrevDesktop(self):
        if not self.desktops:
            return None
        return self.desktops[-1]

    def switchNextDesktop(self):
        if not self.desktops:
            return

        curDesktop = StoredDesktop(self)

        if not curDesktop.empty():
            self.desktops.append(curDesktop)
        newDesktop = self.desktops.pop(0)

        newDesktop.show()

    def switchPrevDesktop(self):
        if not self.desktops:
            return

        curDesktop = StoredDesktop(self)

        if not curDesktop.empty():
            self.desktops.insert(0, curDesktop)
        newDesktop = self.desktops.pop()

        newDesktop.show()

    def newDesktop(self):
        curDesktop = StoredDesktop(self)
        if not curDesktop.empty():
            self.desktops.append(curDesktop)
        pylewm.tiles.newMonitorTile(self.rect)

def getMonitor(forPos):
    if len(forPos) == 4:
        return pylewm.rects.getMostOverlapping(forPos, Monitors, lambda mon: mon.rect)
    elif len(forPos) == 2:
        for mon in Monitors:
            if mon.rect[0] <= forPos[0] and mon.rect[2] >= forPos[0] \
                    and mon.rect[1] <= forPos[1] and mon.rect[3] >= forPos[1]:
                return mon
    return None

def getFocusMonitor():
    win = win32gui.GetForegroundWindow()
    monitor = None

    cursorPos = win32gui.GetCursorPos()
    mouseMonitor = getMonitor(cursorPos)

    if win is None:
        return mouseMonitor
    elif len(pylewm.tiles.getCurrentMonitorTile(cursorPos).childList) == 0:
        return mouseMonitor
    else:
        monitor = getMonitor(win32gui.GetWindowRect(win))
    return monitor

@pyleinit
def initMonitors():
    for mhnd in win32api.EnumDisplayMonitors(None, None):
        info = win32api.GetMonitorInfo(mhnd[0])
        monitor = Monitor(info)
        DesktopArea[0] = min(DesktopArea[0], info['Monitor'][0])
        DesktopArea[1] = min(DesktopArea[1], info['Monitor'][1])
        DesktopArea[2] = max(DesktopArea[2], info['Monitor'][2])
        DesktopArea[3] = max(DesktopArea[3], info['Monitor'][3])
        Monitors.append(monitor)
    pylewm.rects.DesktopArea = DesktopArea
