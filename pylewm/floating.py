from pylewm import pylecommand, pyletick, pyleinit, runpylecommand
import pylewm.focus
import pylewm.style
import pylewm.rects
import pylewm.windows
import win32gui,win32con, win32api
import traceback

FloatingWindows = []
FloatingVisible = True
MonitorRects = []

@pylecommand
def focus_dir(dir="left"):
    """ Switch focus to a window in a particular direction relative to the currently focused window. """
    curWindow = win32gui.GetForegroundWindow()
    if not win32gui.IsWindow(curWindow):
        return
    curRect = win32gui.GetWindowRect(curWindow)
    
    selWin = pylewm.rects.getClosestInDirection(dir, curRect,
        (win for win in FloatingWindows if not win.hidden), 
        lambda win: win32gui.GetWindowRect(win.window), wrap=True,
        ignore=getFloatingWindowFor(curWindow))
    if selWin is not None:
        selWin.focus()

@pylecommand
def focus_next():
    """ Focus the next floating window. """
    if not FloatingWindows:
        return

    curWindow = win32gui.GetForegroundWindow()
    if not win32gui.IsWindow(curWindow):
        focusFloating(0, +1)
        return

    for i, win in enumerate(FloatingWindows):
        if win.window == curWindow:
            focusFloating(i+1, +1)
            return
    focusFloating(0, +1)

@pylecommand
def focus_prev():
    """ Focus the previous floating window. """
    if not FloatingWindows:
        return

    curWindow = win32gui.GetForegroundWindow()
    if not win32gui.IsWindow(curWindow):
        focusFloating(0, +1)
        return

    for i, win in enumerate(FloatingWindows):
        if win.window == curWindow:
            focusFloating(i-1, -1)
            return
    focusFloating(0, +1)

def focusFloating(index, direction):
    for i in range(0, len(FloatingWindows)):
        win = FloatingWindows[(i*direction+index) % len(FloatingWindows)]
        if not win.hidden:
            win.focus()
            break

@pylecommand
def toggle_layer():
    """ Toggle whether the floating layer is visible or not. """
    global FloatingVisible
    if FloatingVisible:
        FloatingVisible = False
        for win in FloatingWindows:
            win.banish()
    else:
        FloatingVisible = True
        for win in FloatingWindows:
            win.summon()
            win.show()

@pylecommand
def move_dir(dir="left", step=200, snap=True):
    """ Move the focused floating window in a particular direction. """
    curWindow = win32gui.GetForegroundWindow()
    if not win32gui.IsWindow(curWindow):
        return
    if not isFloatingWindow(curWindow):
        return

    curRect = list(win32gui.GetWindowRect(curWindow))
    if dir == "left":
        curRect[0] -= step
        curRect[2] -= step
    elif dir == "right":
        curRect[0] += step
        curRect[2] += step
    elif dir == "up":
        curRect[1] -= step
        curRect[3] -= step
    elif dir == "down":
        curRect[1] += step
        curRect[3] += step

    moveWindow(curWindow, curRect, snapTo=snap, snapThrough=snap)

@pylecommand
def grow_dir(dir="left", step=200, snap=True):
    """ Grow the focused floating window in a particular direction. """
    curWindow = win32gui.GetForegroundWindow()
    if not win32gui.IsWindow(curWindow):
        return
    if not isFloatingWindow(curWindow):
        return

    curRect = list(win32gui.GetWindowRect(curWindow))
    if dir == "left":
        curRect[0] -= step
    elif dir == "right":
        curRect[2] += step
    elif dir == "up":
        curRect[1] -= step
    elif dir == "down":
        curRect[3] += step

    moveWindow(curWindow, curRect, snapTo=snap, snapThrough=False, snapResize=True)

@pylecommand
def shrink_dir(dir="left", step=200, snap=True):
    """ Shrink the focused floating window in a particular direction. """
    curWindow = win32gui.GetForegroundWindow()
    if not win32gui.IsWindow(curWindow):
        return
    if not isFloatingWindow(curWindow):
        return

    curRect = list(win32gui.GetWindowRect(curWindow))
    if dir == "left":
        curRect[0] += step
    elif dir == "right":
        curRect[2] -= step
    elif dir == "up":
        curRect[1] += step
    elif dir == "down":
        curRect[3] -= step

    # Make sure we don't become impossibly small
    width = curRect[2] - curRect[0]
    if width < 20:
        curRect[2] += 20 - width
    height = curRect[3] - curRect[1]
    if height < 20:
        curRect[3] += 20 - height

    moveWindow(curWindow, curRect, snapTo=snap, snapThrough=False, snapResize=True)

@pylecommand
def center():
    """ Center the floating window on the monitor."""
    curWindow = win32gui.GetForegroundWindow()
    print("DO CENTER")
    if not win32gui.IsWindow(curWindow):
        return
    if not isFloatingWindow(curWindow):
        return

    curRect = list(win32gui.GetWindowRect(curWindow))
    monitor = pylewm.monitors.getMonitor(curRect)

    width = curRect[2] - curRect[0]
    height = curRect[3] - curRect[1]
    
    monWidth = monitor.rect[2] - monitor.rect[0]
    monHeight = monitor.rect[3] - monitor.rect[1]

    print(f"CENTER FLOATING FROM {curRect}")

    curRect[0] = monitor.rect[0] + int((monWidth - width) / 2)
    curRect[1] = monitor.rect[1] + int((monHeight - height) / 2)
    curRect[2] = curRect[0] + width
    curRect[3] = curRect[1] + height

    print(f"   TO {curRect}")

    moveWindow(curWindow, curRect)

def moveWindow(window, rect, snapTo=False, snapThrough=False, snapResize=False):
    print(f"MOVE FLOATING {win32gui.GetWindowText(window)} TO {rect}")
    if snapTo or snapThrough:
        prevRect = list(win32gui.GetWindowRect(window))
        # Check which monitors intersect the new position
        for monitor in MonitorRects:
            # Ignore the monitor if we're not near it
            if not pylewm.rects.overlaps(prevRect, monitor) and not pylewm.rects.overlaps(rect, monitor):
                continue

            snapped = False
            for dim in range(0, 4):
                otherDim = (dim%2) + (2 if dim < 2 else 0)
                size = rect[otherDim] - rect[dim]

                if dim < 2:
                    wasBefore = prevRect[dim] < monitor[dim]
                    nowBefore = rect[dim] < monitor[dim]
                else:
                    wasBefore = prevRect[dim] > monitor[dim]
                    nowBefore = rect[dim] > monitor[dim]

                if not wasBefore and nowBefore:
                    if abs(monitor[dim] - prevRect[dim]) > 10:
                        if snapTo:
                            # Snap against boundary
                            print(f"SNAP ONTO BOUNDARY AT {dim} = {monitor[dim]}")
                            rect[dim] = monitor[dim]
                            if not snapResize:
                                rect[otherDim] = rect[dim] + size
                            print(f"NEW RECT {rect}")
                            snapped = True
                            break
                    else:
                        if snapThrough:
                            # Snap through boundary
                            checkRect = list(rect)
                            checkRect[otherDim] = monitor[dim]
                            checkRect[dim] = monitor[dim] - size
                            if pylewm.rects.isInDesktopArea(checkRect):
                                print(f"SNAP THROUGH BOUNDARY AT {dim} = {monitor[dim]}")
                                rect = checkRect
                                print(f"NEW RECT {rect}")
                                snapped = True
                                break
            if snapped:
                break

    pylewm.windows.move(window, rect, topmost=True)

@pylecommand
def if_floating(command, *args, **kwargs):
    """ Only execute the passed command if a floating window has focus. """
    if isFloatingFocused():
        runpylecommand(command, *args, **kwargs)
        
def getFloatingWindowFor(hwnd):
    for win in FloatingWindows:
        if win.window == hwnd:
            return win
    return None
    
def isFloatingFocused():
    curWindow = win32gui.GetForegroundWindow()
    return isFloatingWindow(curWindow)

def isFloatingWindow(window):
    # If a child window of a floating window has focus,
    # we consider that as a floating window
    for win in FloatingWindows:
        if win.window == window:
            return True
    parent = win32api.GetWindowLong(window, win32con.GWL_HWNDPARENT)
    if win32gui.IsWindow(parent):
        return isFloatingWindow(parent)
    return False
    
def getClosestFloatingWindow(toRect):
    if not FloatingWindows:
        return None
    return pylewm.rects.getClosestTo(toRect,
        (win for win in FloatingWindows if not win.hidden),
        lambda win: win32gui.GetWindowRect(win.window))

def takeFloatingWindow(floating):
    FloatingWindows.remove(floating)

def returnFloatingWindow(floating):
    FloatingWindows.append(floating)

class FloatingWindow:
    def __init__(self, window):
        self.window = window
        self.wasGone = False
     
        self.show()          
    
    def update(self):
        if not win32gui.IsWindow(self.window):
            return False
        if pylewm.windows.isTaskbarIgnored(self.window):
            return False
        if not pylewm.rects.overlapsDesktopArea(win32gui.GetWindowRect(self.window)):
            self.hidden = True
            self.wasGone = True
        elif self.wasGone:
            self.wasGone = False
            self.hidden = False
        return True

    def isChildOf(self, parent):
        if self.window == parent:
            return True
        if win32gui.IsChild(parent, self.window):
            return True
        return False

    def isChildOf(self, parent):
        check = self.window
        while win32gui.IsWindow(check):
            if check == parent:
                return True
            check = win32api.GetWindowLong(check, win32con.GWL_HWNDPARENT)
        return False
    
    @property
    def title(self):
        return win32gui.GetWindowText(self.window)
        
    def focus(self):
        print(f"FOCUS FLOATING {self.title} hidden:{self.hidden} hwnd:{self.window} iconic:{win32gui.IsIconic(self.window)} {win32gui.IsWindowVisible(self.window)}")
        self.show()
        pylewm.focus.set(self.window)
        
    def show(self):
        # Floating windows are always on top
        print(f"SHOW FLOATING {self.title}")
        self.rect = win32gui.GetWindowRect(self.window)
        if win32gui.IsIconic(self.window):
            win32gui.ShowWindow(self.window, win32con.SW_RESTORE)
        pylewm.windows.move(self.window, self.rect, topmost=True)
        self.hidden = False
        self.wasGone = False
        
    def hide(self):
        print(f"HIDE FLOATING {self.title}")
        self.rect = win32gui.GetWindowRect(self.window)
        pylewm.windows.move(self.window, self.rect, bottom=True)
        self.hidden = True
        self.wasGone = False

    def banish(self):
        pylewm.windows.banish(self.window)

    def summon(self):
        pylewm.windows.summon(self.window)

def hideWithParent(parent):
    for win in FloatingWindows:
        if win.isChildOf(parent):
            win.hide()
    
def showWithParent(parent):
    for win in FloatingWindows:
        if win.isChildOf(parent):
            win.show()
    
def onWindowCreated(window):
    startFloatingWindow(window)

def startFloatingWindow(window):
    floating = FloatingWindow(window)
    if not FloatingVisible:
        floating.banish()
    FloatingWindows.append(floating)

def stopFloatingWindow(window, keepFloatingFocus=False):
    for win in FloatingWindows:
        if win.window == window:
            if not FloatingVisible:
                win.summon()
            win.hide()
            FloatingWindows.remove(win)
            if keepFloatingFocus and win32gui.GetForegroundWindow() == win:
                closest = getClosestFloatingWindow(win32gui.GetWindowRect(win))
                if closest is not None:
                    closest.focus()
                    return True
                return False
            return None
    return None

def print_list():
    for win in FloatingWindows:
        print(f"Floating: {win.window} {win.title} AT {win.rect} HIDDEN {win.hidden}")
    
@pyletick
def tickFloating():
    for win in FloatingWindows[:]:
        if not win.update():
            FloatingWindows.remove(win)

@pyleinit
def initFloating():
    for mhnd in win32api.EnumDisplayMonitors(None, None):
        info = win32api.GetMonitorInfo(mhnd[0])
        MonitorRects.append(info['Monitor'])
