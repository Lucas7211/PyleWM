from pylewm import pylecommand, pyletick
import pylewm.focus
import pylewm.style
import pylewm.rects
import pylewm.windows
import win32gui,win32con, win32api

FloatingWindows = []
FloatingVisible = True

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
        win32gui.SetWindowPos(self.window, win32con.HWND_TOPMOST,
                        self.rect[0], self.rect[1],
                        self.rect[2] - self.rect[0], self.rect[3] - self.rect[1],
                        win32con.SWP_NOACTIVATE)
        self.hidden = False
        self.wasGone = False
        
    def hide(self):
        print(f"HIDE FLOATING {self.title}")
        self.rect = win32gui.GetWindowRect(self.window)
        win32gui.SetWindowPos(self.window, win32con.HWND_BOTTOM,
                        self.rect[0], self.rect[1],
                        self.rect[2] - self.rect[0], self.rect[3] - self.rect[1],
                        win32con.SWP_NOACTIVATE)
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
