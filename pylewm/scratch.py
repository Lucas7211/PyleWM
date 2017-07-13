import pylewm
import pylewm.tiles
import pylewm.floating
import pylewm.windows
import pylewm.monitors

import win32gui, win32api, win32con

Stack = []

class YankedWindow:
    def __init__(self, window, wasFloating):
        self.window = window
        self.wasFloating = wasFloating
        if self.wasFloating:
            self.relRect = list(win32gui.GetWindowRect(window))
            monitorRect = pylewm.monitors.getMonitor(self.relRect).rect
            for i in range(0,4):
                offset = monitorRect[(i%2)]
                size = monitorRect[2+(i%2)] - offset
                self.relRect[i] = float(self.relRect[i] - offset) / float(size)

    def drop(self):
        if self.wasFloating:
            # Move the window to the same relative floating position on the new monitor
            monitor = pylewm.monitors.getFocusMonitor()
            monitorRect = monitor.rect
            rect = []
            for i in range(0,4):
                offset = monitorRect[(i%2)]
                size = monitorRect[2+(i%2)] - offset
                rect.append(int(self.relRect[i] * float(size)) + offset)

            pylewm.windows.summon(self.window)

            print(f"DROP WINDOW {self.relRect} TO {rect} ON MONITOR {monitorRect}")
            pylewm.windows.move(self.window, rect)
            pylewm.floating.startFloatingWindow(self.window)
        else:
            pylewm.windows.summon(self.window)
            pylewm.tiles.startTilingWindow(self.window)

@pylewm.pylecommand
def yank():
    """ Yank the currently focused window out of window management so it can be dropped back later. """

    curWindow = win32gui.GetForegroundWindow()
    if not win32gui.IsWindow(curWindow):
        return

    yanked = None
    if pylewm.floating.isFloatingWindow(curWindow):
        print(f"Yank floating {curWindow} {win32gui.GetWindowText(curWindow)}")
        yanked = YankedWindow(curWindow, True)
        pylewm.floating.stopFloatingWindow(curWindow, keepFloatingFocus=True)
    else:
        print(f"Yank tiled {curWindow} {win32api.GetWindowLong(curWindow, win32con.GWL_HWNDPARENT)} {win32gui.GetWindowText(curWindow)}")
        yanked = YankedWindow(curWindow, False)
        pylewm.tiles.stopTilingWindow(curWindow, keepTilingFocus=True)

    pylewm.windows.banish(curWindow)
    Stack.insert(0, yanked)

@pylewm.pylecommand
def drop():
    """ Drop the latest window to be yanked where the current focus is. """
    if Stack:
        Stack.pop(0).drop()

@pylewm.pylecommand
def drop_all():
    """ Drop all yanked windows where the current focus is. """
    for yanked in Stack:
        yanked.drop()
    del Stack[:]
